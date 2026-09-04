"""
XGBoost Training Pipeline
Trains a classical ML baseline model with reproducible splitting, feature extraction,
hyperparameter tracking, and structured experiment logging.
"""

import os
import sys
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
import xgboost as xgb

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.ml import (
    SplitConfig,
    FeatureConfig,
    XGBConfig,
    ExperimentMetadata,
)
from backend.app.ml.splitter import DatasetSplitter
from backend.app.ml.features import FeatureExtractor
from backend.app.utils.metrics import compute_regression_metrics


def compute_file_hash(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def train_xgboost(
    dataset_path: Path,
    experiment_name: str = "xgboost_baseline",
    split_config: SplitConfig = None,
    feature_config: FeatureConfig = None,
    xgb_config: XGBConfig = None,
) -> Tuple[xgb.XGBRegressor, ExperimentMetadata]:
    split_config = split_config or SplitConfig()
    feature_config = feature_config or FeatureConfig()
    xgb_config = xgb_config or XGBConfig()

    start_time = time.time()
    dataset_hash = compute_file_hash(dataset_path)

    logger.info(f"Loading processed dataset: {dataset_path} (hash: {dataset_hash})")
    df = pd.read_csv(dataset_path, dtype={"fingerprint": str})

    # 1. Reproducible split
    splitter = DatasetSplitter(split_config)
    train_df, val_df, test_df = splitter.split(df)
    logger.info(
        f"Data split: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}"
    )

    # 2. Feature extraction
    extractor = FeatureExtractor(feature_config)
    X_train, y_train, feature_names = extractor.extract(train_df)
    X_val, y_val, _ = extractor.extract(val_df)
    X_test, y_test, _ = extractor.extract(test_df)

    # 3. Model initialization
    model = xgb.XGBRegressor(
        n_estimators=xgb_config.n_estimators,
        learning_rate=xgb_config.learning_rate,
        max_depth=xgb_config.max_depth,
        subsample=xgb_config.subsample,
        colsample_bytree=xgb_config.colsample_bytree,
        random_state=xgb_config.random_seed,
        early_stopping_rounds=xgb_config.early_stopping_rounds,
        eval_metric="rmse",
    )

    # 4. Fit model
    logger.info("Training XGBoost regressor...")
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False,
    )

    # 5. Evaluate
    y_val_pred = model.predict(X_val)
    y_test_pred = model.predict(X_test)

    metrics_val = compute_regression_metrics(y_val, y_val_pred)
    metrics_test = compute_regression_metrics(y_test, y_test_pred)

    duration = time.time() - start_time
    logger.info(
        f"Training complete in {duration:.2f}s | Val RMSE: {metrics_val['rmse']} | Test RMSE: {metrics_test['rmse']}"
    )

    # 6. Feature Importance (top 15)
    importances = model.feature_importances_
    feat_imp = {
        name: float(imp)
        for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:15]
    }

    # 7. Persist Model and Metadata
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    model_filename = f"{experiment_name}_{timestamp}.json"
    model_artifact_path = settings.MODELS_DIR / model_filename
    model.save_model(str(model_artifact_path))

    # Also save as 'latest' for API convenience
    latest_model_path = settings.MODELS_DIR / "xgboost_esol_latest.json"
    model.save_model(str(latest_model_path))

    experiment_id = f"EXP-XGB-{timestamp}"
    meta = ExperimentMetadata(
        experiment_id=experiment_id,
        experiment_name=experiment_name,
        model_type="xgboost",
        task_type="regression",
        dataset_name=dataset_path.stem,
        dataset_hash=dataset_hash,
        split_config=split_config.model_dump(),
        feature_config=feature_config.model_dump(),
        hyperparameters=xgb_config.model_dump(),
        metrics_val=metrics_val,
        metrics_test=metrics_test,
        training_duration_seconds=round(duration, 3),
        model_artifact_path=str(model_artifact_path),
        created_at=datetime.now(timezone.utc).isoformat(),
        feature_importance=feat_imp,
    )

    exp_file = settings.EXPERIMENTS_DIR / f"{experiment_id}.json"
    with open(exp_file, "w", encoding="utf-8") as f:
        json.dump(meta.model_dump(), f, indent=2)

    return model, meta


def main():
    parser = argparse.ArgumentParser(description="Train XGBoost Molecular Model")
    parser.add_argument(
        "--dataset",
        "-d",
        type=str,
        default="data/processed/esol_processed.csv",
        help="Path to processed dataset CSV",
    )
    parser.add_argument("--name", "-n", type=str, default="xgboost_esol_baseline", help="Experiment name")
    parser.add_argument("--n-estimators", type=int, default=150, help="Number of trees")
    parser.add_argument("--lr", type=float, default=0.05, help="Learning rate")
    parser.add_argument("--max-depth", type=int, default=4, help="Max tree depth")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error(f"Dataset path does not exist: {dataset_path}")
        sys.exit(1)

    xgb_cfg = XGBConfig(
        n_estimators=args.n_estimators,
        learning_rate=args.lr,
        max_depth=args.max_depth,
        random_seed=args.seed,
    )
    model, meta = train_xgboost(
        dataset_path=dataset_path,
        experiment_name=args.name,
        xgb_config=xgb_cfg,
    )

    print("\n================ XGBOOST TRAINING REPORT ================")
    print(f"Experiment ID:    {meta.experiment_id}")
    print(f"Dataset:          {meta.dataset_name} (hash: {meta.dataset_hash})")
    print(f"Val RMSE:         {meta.metrics_val['rmse']} | R2: {meta.metrics_val['r2']}")
    print(f"Test RMSE:        {meta.metrics_test['rmse']} | R2: {meta.metrics_test['r2']}")
    print(f"Model Artifact:   {meta.model_artifact_path}")
    print("Top Features:")
    for feat, imp in list(meta.feature_importance.items())[:5]:
        print(f"  - {feat:20s}: {imp:.4f}")
    print("=========================================================\n")


if __name__ == "__main__":
    main()
