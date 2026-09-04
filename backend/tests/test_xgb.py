"""
Unit tests for XGBoost Classical ML Pipeline (Phase 2)
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from backend.app.schemas.ml import SplitConfig, FeatureConfig, XGBConfig
from backend.app.ml.splitter import DatasetSplitter
from backend.app.ml.features import FeatureExtractor
from backend.app.ml.train_xgb import train_xgboost
from backend.app.ml.evaluate_xgb import load_xgboost_model, predict_smiles
from backend.app.utils.metrics import compute_regression_metrics, compute_classification_metrics


def test_split_reproducibility():
    df = pd.DataFrame({
        "id": range(100),
        "smiles": ["CC"] * 100,
        "target": np.random.randn(100)
    })

    splitter_1 = DatasetSplitter(SplitConfig(random_seed=42))
    train_1, val_1, test_1 = splitter_1.split(df)

    splitter_2 = DatasetSplitter(SplitConfig(random_seed=42))
    train_2, val_2, test_2 = splitter_2.split(df)

    assert train_1.equals(train_2)
    assert val_1.equals(val_2)
    assert test_1.equals(test_2)
    assert len(train_1) == 80
    assert len(val_1) == 10
    assert len(test_1) == 10


def test_regression_metrics():
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 1.9, 3.2, 3.8])

    metrics = compute_regression_metrics(y_true, y_pred)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert metrics["rmse"] > 0
    assert metrics["r2"] > 0.9


def test_train_xgboost_pipeline(tmp_path):
    dataset_path = Path("data/processed/esol_processed.csv")
    assert dataset_path.exists()

    xgb_cfg = XGBConfig(n_estimators=30, learning_rate=0.1, max_depth=3, random_seed=42)
    model, meta = train_xgboost(
        dataset_path=dataset_path,
        experiment_name="test_xgb_exp",
        xgb_config=xgb_cfg,
    )

    assert model is not None
    assert meta.model_type == "xgboost"
    assert "rmse" in meta.metrics_val
    assert "rmse" in meta.metrics_test
    assert Path(meta.model_artifact_path).exists()


def test_xgboost_prediction():
    latest_model_path = Path("models/xgboost_esol_latest.json")
    if not latest_model_path.exists():
        dataset_path = Path("data/processed/esol_processed.csv")
        train_xgboost(dataset_path=dataset_path, experiment_name="init_model")

    aspirin = "CC(=O)Oc1ccccc1C(=O)O"
    pred = predict_smiles(aspirin, latest_model_path)

    assert pred.smiles == aspirin
    assert pred.canonical_smiles is not None
    assert isinstance(pred.predicted_value, float)
    assert pred.unit == "log mol/L"
    assert "molecular_weight" in pred.descriptors
