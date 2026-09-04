"""
Experiment endpoints
"""

import json
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.services.repository import ExperimentRepository
from backend.app.ml.compare import load_latest_experiments, generate_comparison_report

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.get("")
def list_experiments(db: Session = Depends(get_db)):
    repo = ExperimentRepository(db)
    db_exps = repo.list_experiments()
    if db_exps:
        return [
            {
                "id": exp.id,
                "name": exp.name,
                "model_id": exp.model_id,
                "dataset_id": exp.dataset_id,
                "status": exp.status,
                "metrics_test": exp.metrics_test,
                "training_duration_seconds": exp.training_duration_seconds,
            }
            for exp in db_exps
        ]

    # Disk experiments fallback
    exp_files = list(settings.EXPERIMENTS_DIR.glob("EXP-*.json"))
    result = []
    for p in exp_files:
        try:
            with open(p, "r", encoding="utf-8") as f:
                result.append(json.load(f))
        except Exception:
            pass
    return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)


@router.get("/comparison/latest")
def get_model_comparison():
    comp_file = settings.EXPERIMENTS_DIR / "model_comparison_esol.json"
    if comp_file.exists():
        with open(comp_file, "r", encoding="utf-8") as f:
            return json.load(f)

    xgb_exp, gnn_exp = load_latest_experiments()
    if not xgb_exp or not gnn_exp:
        raise HTTPException(status_code=404, detail="Both XGBoost and GNN experiments required for comparison")

    return generate_comparison_report(xgb_exp, gnn_exp)


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    # Check disk first for rich payload
    exp_path = settings.EXPERIMENTS_DIR / f"{experiment_id}.json"
    if exp_path.exists():
        with open(exp_path, "r", encoding="utf-8") as f:
            return json.load(f)

    repo = ExperimentRepository(db)
    exp = repo.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "id": exp.id,
        "name": exp.name,
        "model_id": exp.model_id,
        "status": exp.status,
        "hyperparameters": exp.hyperparameters,
        "feature_config": exp.feature_config,
        "metrics_val": exp.metrics_val,
        "metrics_test": exp.metrics_test,
        "training_duration_seconds": exp.training_duration_seconds,
    }
