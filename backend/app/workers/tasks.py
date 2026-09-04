"""
Celery Background Task Definitions
Distributed worker tasks for compute-intensive molecular modeling and asynchronous jobs.
"""

from pathlib import Path
from typing import Dict, Any

from backend.app.workers.celery_app import celery_app
from backend.app.ml.evaluate_xgb import predict_smiles
from backend.app.ml.train_gnn import predict_gnn_smiles, train_gnn
from backend.app.ml.train_xgb import train_xgboost
from backend.app.core.logging import logger


@celery_app.task(bind=True, name="tasks.predict_molecule")
def predict_molecule_task(self, smiles: str, model_type: str = "xgboost") -> Dict[str, Any]:
    """Execute molecular prediction inside worker process."""
    logger.info(f"Task {self.request.id}: starting prediction for {smiles} with {model_type}")
    if model_type.lower() == "gnn":
        pred_val = predict_gnn_smiles(smiles)
        return {"smiles": smiles, "model_type": "gnn", "predicted_value": round(pred_val, 4), "unit": "log mol/L"}
    else:
        res = predict_smiles(smiles)
        return res.model_dump()


@celery_app.task(bind=True, name="tasks.train_model")
def train_model_task(self, dataset_path: str, model_type: str = "xgboost") -> Dict[str, Any]:
    """Execute model training inside worker process."""
    path = Path(dataset_path)
    logger.info(f"Task {self.request.id}: training {model_type} on {dataset_path}")
    if model_type.lower() == "gnn":
        _, meta = train_gnn(dataset_path=path, epochs=30)
        return meta.model_dump()
    else:
        _, meta = train_xgboost(dataset_path=path)
        return meta.model_dump()
