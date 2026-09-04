"""
Machine Learning Schemas & Experiment Tracking Models
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SplitConfig(BaseModel):
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    random_seed: int = 42
    stratify: bool = False


class FeatureConfig(BaseModel):
    use_descriptors: bool = True
    use_fingerprints: bool = True
    fingerprint_bits: int = 1024


class XGBConfig(BaseModel):
    n_estimators: int = 100
    learning_rate: float = 0.05
    max_depth: int = 4
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    early_stopping_rounds: int = 10
    random_seed: int = 42


class ExperimentMetadata(BaseModel):
    experiment_id: str
    experiment_name: str
    model_type: str  # "xgboost" or "gnn"
    task_type: str = "regression"  # "regression" or "classification"
    dataset_name: str
    dataset_hash: str
    split_config: Dict[str, Any]
    feature_config: Dict[str, Any]
    hyperparameters: Dict[str, Any]
    metrics_val: Dict[str, float]
    metrics_test: Dict[str, float]
    training_duration_seconds: float
    model_artifact_path: str
    created_at: str
    feature_importance: Optional[Dict[str, float]] = None


class PredictionRequest(BaseModel):
    smiles: str
    model_id: Optional[str] = "xgboost_esol_latest"


class PredictionResponse(BaseModel):
    smiles: str
    canonical_smiles: str
    predicted_value: float
    unit: str = "log mol/L"
    model_id: str
    descriptors: Dict[str, float]
