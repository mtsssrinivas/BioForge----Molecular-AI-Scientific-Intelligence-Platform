"""
Prediction endpoints
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.ml import PredictionRequest, PredictionResponse
from backend.app.services.repository import PredictionRepository, ExperimentRepository

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("", response_model=PredictionResponse)
def create_prediction(req: PredictionRequest, db: Session = Depends(get_db)):
    from backend.app.ml.evaluate_xgb import predict_smiles
    t0 = time.time()
    try:
        res = predict_smiles(req.smiles)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

    duration_ms = (time.time() - t0) * 1000.0

    # Persist in DB
    try:
        exp_repo = ExperimentRepository(db)
        model = exp_repo.get_or_create_model(
            model_id=res.model_id,
            name=res.model_id,
            model_type="xgboost",
            artifact_path=f"models/{res.model_id}.json",
        )
        pred_repo = PredictionRepository(db)
        pred_repo.record_prediction(
            model_id=model.id,
            input_smiles=res.smiles,
            canonical_smiles=res.canonical_smiles,
            predicted_value=res.predicted_value,
            unit=res.unit,
            inference_time_ms=round(duration_ms, 2),
        )
    except Exception:
        pass

    return res


@router.get("/{prediction_id}")
def get_prediction(prediction_id: str, db: Session = Depends(get_db)):
    repo = PredictionRepository(db)
    pred = repo.get_prediction(prediction_id)
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {
        "id": pred.id,
        "input_smiles": pred.input_smiles,
        "canonical_smiles": pred.canonical_smiles,
        "predicted_value": pred.predicted_value,
        "unit": pred.unit,
        "inference_time_ms": pred.inference_time_ms,
        "created_at": pred.created_at.isoformat() if pred.created_at else None,
    }
