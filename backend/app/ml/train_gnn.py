"""
PyTorch GNN Training and Evaluation Pipeline
Trains a molecular Graph Neural Network on the exact same dataset split as the classical XGBoost baseline.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Dict, Any, List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.ml import SplitConfig, ExperimentMetadata
from backend.app.ml.splitter import DatasetSplitter
from backend.app.ml.gnn_dataset import (
    MolecularDataset,
    collate_molecular_graphs,
    mol_to_graph,
    BatchMolecularGraph,
)
from backend.app.ml.gnn_model import MolecularGNN
from backend.app.ml.train_xgb import compute_file_hash
from backend.app.utils.metrics import compute_regression_metrics


def train_gnn(
    dataset_path: Path,
    experiment_name: str = "gnn_esol_model",
    split_config: SplitConfig = None,
    epochs: int = 60,
    batch_size: int = 16,
    lr: float = 0.003,
    hidden_dim: int = 64,
    num_layers: int = 3,
    dropout: float = 0.1,
    seed: int = 42,
) -> Tuple[MolecularGNN, ExperimentMetadata]:
    split_config = split_config or SplitConfig(random_seed=seed)

    # Set seeds for reproducibility
    torch.manual_seed(seed)
    np.random.seed(seed)

    start_time = time.time()
    dataset_hash = compute_file_hash(dataset_path)

    logger.info(f"Loading dataset for GNN training: {dataset_path} (hash: {dataset_hash})")
    df = pd.read_csv(dataset_path, dtype={"fingerprint": str})

    # Exact identical split as XGBoost
    splitter = DatasetSplitter(split_config)
    train_df, val_df, test_df = splitter.split(df)
    logger.info(f"Identical split loaded: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    train_dataset = MolecularDataset(train_df["canonical_smiles"].tolist(), train_df["target"].tolist())
    val_dataset = MolecularDataset(val_df["canonical_smiles"].tolist(), val_df["target"].tolist())
    test_dataset = MolecularDataset(test_df["canonical_smiles"].tolist(), test_df["target"].tolist())

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_molecular_graphs)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_molecular_graphs)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_molecular_graphs)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MolecularGNN(
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=5)
    criterion = nn.MSELoss()

    best_val_loss = float("inf")
    best_state = None
    patience = 12
    patience_counter = 0

    loss_history = {"train": [], "val": []}

    logger.info(f"Training GNN for up to {epochs} epochs on {device}...")
    for epoch in range(1, epochs + 1):
        # Training loop
        model.train()
        train_losses = []
        for batch in train_loader:
            x = batch.x.to(device)
            edge_index = batch.edge_index.to(device)
            edge_attr = batch.edge_attr.to(device)
            batch_idx = batch.batch.to(device)
            y = batch.y.to(device)

            optimizer.zero_grad()
            preds = model(x, edge_index, edge_attr, batch_idx, batch.num_graphs)
            loss = criterion(preds, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            train_losses.append(loss.item())

        avg_train_loss = float(np.mean(train_losses))

        # Validation loop
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                x = batch.x.to(device)
                edge_index = batch.edge_index.to(device)
                edge_attr = batch.edge_attr.to(device)
                batch_idx = batch.batch.to(device)
                y = batch.y.to(device)

                preds = model(x, edge_index, edge_attr, batch_idx, batch.num_graphs)
                loss = criterion(preds, y)
                val_losses.append(loss.item())

        avg_val_loss = float(np.mean(val_losses))
        scheduler.step(avg_val_loss)

        loss_history["train"].append(round(avg_train_loss, 4))
        loss_history["val"].append(round(avg_val_loss, 4))

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= patience:
            logger.info(f"Early stopping triggered at epoch {epoch}")
            break

    # Load best model weights
    if best_state is not None:
        model.load_state_dict(best_state)
    model.to(device)
    model.eval()

    # Evaluation on validation set
    def evaluate_loader(loader):
        all_true = []
        all_pred = []
        with torch.no_grad():
            for batch in loader:
                x = batch.x.to(device)
                edge_index = batch.edge_index.to(device)
                edge_attr = batch.edge_attr.to(device)
                batch_idx = batch.batch.to(device)
                preds = model(x, edge_index, edge_attr, batch_idx, batch.num_graphs)
                all_pred.extend(preds.cpu().numpy().tolist())
                all_true.extend(batch.y.cpu().numpy().tolist())
        return compute_regression_metrics(np.array(all_true), np.array(all_pred))

    metrics_val = evaluate_loader(val_loader)
    metrics_test = evaluate_loader(test_loader)

    duration = time.time() - start_time
    logger.info(
        f"GNN Training complete in {duration:.2f}s | Val RMSE: {metrics_val['rmse']} | Test RMSE: {metrics_test['rmse']}"
    )

    # Persist model
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    artifact_path = settings.MODELS_DIR / f"{experiment_name}_{timestamp}.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "dropout": dropout,
            "metrics_test": metrics_test,
        },
        str(artifact_path),
    )

    latest_path = settings.MODELS_DIR / "gnn_esol_latest.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "dropout": dropout,
            "metrics_test": metrics_test,
        },
        str(latest_path),
    )

    experiment_id = f"EXP-GNN-{timestamp}"
    meta = ExperimentMetadata(
        experiment_id=experiment_id,
        experiment_name=experiment_name,
        model_type="gnn",
        task_type="regression",
        dataset_name=dataset_path.stem,
        dataset_hash=dataset_hash,
        split_config=split_config.model_dump(),
        feature_config={"representation": "molecular_graph", "node_dim": 20, "edge_dim": 7},
        hyperparameters={
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": lr,
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "dropout": dropout,
            "random_seed": seed,
            "loss_history": loss_history,
        },
        metrics_val=metrics_val,
        metrics_test=metrics_test,
        training_duration_seconds=round(duration, 3),
        model_artifact_path=str(artifact_path),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    exp_file = settings.EXPERIMENTS_DIR / f"{experiment_id}.json"
    with open(exp_file, "w", encoding="utf-8") as f:
        json.dump(meta.model_dump(), f, indent=2)

    return model, meta


def predict_gnn_smiles(smiles: str, checkpoint_path: Path = None) -> float:
    checkpoint_path = checkpoint_path or (settings.MODELS_DIR / "gnn_esol_latest.pt")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"GNN checkpoint not found: {checkpoint_path}")

    checkpoint = torch.load(str(checkpoint_path), map_location="cpu")
    model = MolecularGNN(
        hidden_dim=checkpoint.get("hidden_dim", 64),
        num_layers=checkpoint.get("num_layers", 3),
        dropout=0.0,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    graph = mol_to_graph(smiles)
    if graph is None:
        raise ValueError(f"Cannot construct graph for SMILES: {smiles}")

    batch = collate_molecular_graphs([graph])
    with torch.no_grad():
        pred = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch, 1)
    return float(pred.item())


def main():
    parser = argparse.ArgumentParser(description="Train Molecular Graph Neural Network")
    parser.add_argument("--dataset", "-d", type=str, default="data/processed/esol_processed.csv")
    parser.add_argument("--epochs", "-e", type=int, default=70)
    parser.add_argument("--lr", type=float, default=0.003)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    model, meta = train_gnn(
        dataset_path=Path(args.dataset),
        epochs=args.epochs,
        lr=args.lr,
        hidden_dim=args.hidden_dim,
        seed=args.seed,
    )

    print("\n================== GNN TRAINING REPORT ==================")
    print(f"Experiment ID:    {meta.experiment_id}")
    print(f"Val RMSE:         {meta.metrics_val['rmse']} | R2: {meta.metrics_val['r2']}")
    print(f"Test RMSE:        {meta.metrics_test['rmse']} | R2: {meta.metrics_test['r2']}")
    print(f"Model Artifact:   {meta.model_artifact_path}")
    print("=========================================================\n")


if __name__ == "__main__":
    main()
