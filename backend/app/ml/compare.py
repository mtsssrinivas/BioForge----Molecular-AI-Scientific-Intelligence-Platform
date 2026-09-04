"""
Model Comparison Module (XGBoost vs GNN)
Audits experiments performed on the identical dataset split and generates an objective benchmark report.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from backend.app.core.config import settings
from backend.app.core.logging import logger


def load_latest_experiments() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    experiments = list(settings.EXPERIMENTS_DIR.glob("EXP-*.json"))
    if not experiments:
        raise FileNotFoundError("No experiment metadata found in experiments/ directory.")

    xgb_exps = []
    gnn_exps = []

    for p in experiments:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("model_type") == "xgboost":
                xgb_exps.append(data)
            elif data.get("model_type") == "gnn":
                gnn_exps.append(data)

    latest_xgb = sorted(xgb_exps, key=lambda x: x["created_at"])[-1] if xgb_exps else None
    latest_gnn = sorted(gnn_exps, key=lambda x: x["created_at"])[-1] if gnn_exps else None

    return latest_xgb, latest_gnn


def generate_comparison_report(xgb_exp: Dict[str, Any], gnn_exp: Dict[str, Any]) -> Dict[str, Any]:
    if xgb_exp["dataset_hash"] != gnn_exp["dataset_hash"]:
        logger.warning("Models were trained on different dataset versions! Comparison validity compromised.")

    if xgb_exp["split_config"] != gnn_exp["split_config"]:
        logger.warning("Split configurations differ! Models must use identical splits.")

    xgb_metrics = xgb_exp["metrics_test"]
    gnn_metrics = gnn_exp["metrics_test"]

    # Lower RMSE is better
    better_rmse_model = "XGBoost" if xgb_metrics["rmse"] <= gnn_metrics["rmse"] else "GNN"
    # Higher R2 is better
    better_r2_model = "XGBoost" if xgb_metrics["r2"] >= gnn_metrics["r2"] else "GNN"

    report = {
        "dataset_name": xgb_exp["dataset_name"],
        "dataset_hash": xgb_exp["dataset_hash"],
        "split_identical": xgb_exp["split_config"] == gnn_exp["split_config"],
        "models": {
            "xgboost": {
                "experiment_id": xgb_exp["experiment_id"],
                "model_type": "XGBoost (RDKit Descriptors + Morgan FP)",
                "metrics_test": xgb_metrics,
                "training_duration_seconds": xgb_exp["training_duration_seconds"],
                "artifact": xgb_exp["model_artifact_path"],
            },
            "gnn": {
                "experiment_id": gnn_exp["experiment_id"],
                "model_type": "PyTorch Message-Passing GNN",
                "metrics_test": gnn_metrics,
                "training_duration_seconds": gnn_exp["training_duration_seconds"],
                "artifact": gnn_exp["model_artifact_path"],
            },
        },
        "summary": {
            "lower_test_rmse_winner": better_rmse_model,
            "higher_test_r2_winner": better_r2_model,
            "rmse_difference": round(abs(xgb_metrics["rmse"] - gnn_metrics["rmse"]), 4),
            "r2_difference": round(abs(xgb_metrics["r2"] - gnn_metrics["r2"]), 4),
        },
    }

    # Save comparison artifact
    comp_file = settings.EXPERIMENTS_DIR / "model_comparison_esol.json"
    with open(comp_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def main():
    xgb_exp, gnn_exp = load_latest_experiments()
    if not xgb_exp or not gnn_exp:
        print("Both XGBoost and GNN experiments must be run before comparing.")
        return

    report = generate_comparison_report(xgb_exp, gnn_exp)

    print("\n================ CONTROLLED MODEL BENCHMARK REPORT ================")
    print(f"Dataset:            {report['dataset_name']} (Split Identical: {report['split_identical']})")
    print("-" * 68)
    print(f"{'Metric':<18} | {'XGBoost Baseline':<20} | {'PyTorch GNN':<20}")
    print("-" * 68)
    print(
        f"{'Test RMSE (lower)':<18} | {report['models']['xgboost']['metrics_test']['rmse']:<20} | {report['models']['gnn']['metrics_test']['rmse']:<20}"
    )
    print(
        f"{'Test MAE (lower)':<18} | {report['models']['xgboost']['metrics_test']['mae']:<20} | {report['models']['gnn']['metrics_test']['mae']:<20}"
    )
    print(
        f"{'Test R2 (higher)':<18} | {report['models']['xgboost']['metrics_test']['r2']:<20} | {report['models']['gnn']['metrics_test']['r2']:<20}"
    )
    print(
        f"{'Train Time (s)':<18} | {report['models']['xgboost']['training_duration_seconds']:<20} | {report['models']['gnn']['training_duration_seconds']:<20}"
    )
    print("-" * 68)
    print(f"Outcome Winner:     {report['summary']['lower_test_rmse_winner']} achieved lower Test RMSE.")
    print(f"Saved Report:       experiments/model_comparison_esol.json")
    print("===================================================================\n")


if __name__ == "__main__":
    main()
