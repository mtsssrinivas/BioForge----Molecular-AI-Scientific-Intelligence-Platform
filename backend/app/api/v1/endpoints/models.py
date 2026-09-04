"""
Model registry endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models import MLModelRecord

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("")
def list_models(db: Session = Depends(get_db)):
    defaults = {
        "xgboost_esol_latest": {
            "id": "xgboost_esol_latest",
            "name": "XGBoost ESOL Baseline",
            "model_type": "xgboost",
            "framework": "xgboost",
            "version": "v1.0",
            "is_active": True,
        },
        "gnn_esol_latest": {
            "id": "gnn_esol_latest",
            "name": "PyTorch Message-Passing GNN",
            "model_type": "gnn",
            "framework": "pytorch",
            "version": "v1.0",
            "is_active": True,
        },
    }
    stmt = select(MLModelRecord)
    db_models = db.scalars(stmt).all()
    for m in db_models:
        defaults[m.id] = {
            "id": m.id,
            "name": m.name,
            "model_type": m.model_type,
            "framework": m.framework,
            "version": m.version,
            "is_active": m.is_active,
        }
    return list(defaults.values())


@router.get("/{model_id}")
def get_model(model_id: str, db: Session = Depends(get_db)):
    model = db.get(MLModelRecord, model_id)
    if not model:
        if model_id in ("xgboost_esol_latest", "gnn_esol_latest"):
            return {
                "id": model_id,
                "name": "XGBoost ESOL Baseline" if "xgb" in model_id else "PyTorch GNN",
                "model_type": "xgboost" if "xgb" in model_id else "gnn",
                "framework": "xgboost" if "xgb" in model_id else "pytorch",
                "version": "v1.0",
                "is_active": True,
            }
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": model.id,
        "name": model.name,
        "model_type": model.model_type,
        "framework": model.framework,
        "version": model.version,
        "is_active": model.is_active,
    }
