import pytest
import torch
import numpy as np
from pathlib import Path

from backend.app.ml.gnn_dataset import (
    mol_to_graph,
    collate_molecular_graphs,
    NODE_DIM,
    EDGE_DIM,
)
from backend.app.ml.gnn_model import MolecularGNN
from backend.app.ml.train_gnn import train_gnn, predict_gnn_smiles


def test_graph_construction():
    aspirin = "CC(=O)Oc1ccccc1C(=O)O"
    graph = mol_to_graph(aspirin, target=-1.31)

    assert graph is not None
    assert graph.x.dim() == 2
    assert graph.x.size(1) == NODE_DIM
    assert graph.edge_attr.size(1) == EDGE_DIM
    assert graph.edge_index.size(0) == 2
    assert graph.y is not None
    assert graph.num_nodes == 13  # 13 heavy atoms in aspirin


def test_graph_batching_and_forward_pass():
    graphs = [
        mol_to_graph("c1ccccc1", target=-2.13),  # Benzene
        mol_to_graph("CCO", target=0.5),         # Ethanol
    ]
    batch = collate_molecular_graphs(graphs)
    assert batch.num_graphs == 2
    assert batch.batch.size(0) == sum(g.num_nodes for g in graphs)

    model = MolecularGNN(hidden_dim=32, num_layers=2)
    model.eval()
    with torch.no_grad():
        preds = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch, batch.num_graphs)

    assert preds.size(0) == 2
    assert not torch.isnan(preds).any()


def test_gnn_training_and_saving():
    dataset_path = Path("data/processed/esol_processed.csv")
    assert dataset_path.exists()

    model, meta = train_gnn(
        dataset_path=dataset_path,
        experiment_name="test_gnn_exp",
        epochs=5,
        batch_size=16,
        hidden_dim=32,
        num_layers=2,
    )

    assert model is not None
    assert meta.model_type == "gnn"
    assert "rmse" in meta.metrics_val
    assert "rmse" in meta.metrics_test
    assert Path(meta.model_artifact_path).exists()


def test_gnn_prediction():
    latest_pt = Path("models/gnn_esol_latest.pt")
    if not latest_pt.exists():
        dataset_path = Path("data/processed/esol_processed.csv")
        train_gnn(dataset_path=dataset_path, experiment_name="init_gnn", epochs=3)

    pred_val = predict_gnn_smiles("CCO", latest_pt)
    assert isinstance(pred_val, float)
    assert not np.isnan(pred_val)
