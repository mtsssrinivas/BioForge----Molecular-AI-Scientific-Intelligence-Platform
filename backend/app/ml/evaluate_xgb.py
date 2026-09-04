"""
XGBoost Evaluation and Prediction CLI
Evaluates saved XGBoost models on datasets or computes single-molecule predictions.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import xgboost as xgb

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.ml import FeatureConfig, PredictionResponse
from backend.app.ml.features import FeatureExtractor
from backend.app.ml.splitter import DatasetSplitter
from backend.app.utils.metrics import compute_regression_metrics
from backend.app.utils.rdkit_utils import (
    parse_smiles,
    canonicalize_smiles,
    compute_molecular_descriptors,
    compute_morgan_fingerprint,
)


def load_xgboost_model(model_path: Path) -> xgb.XGBRegressor:
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at: {model_path}")
    model = xgb.XGBRegressor()
    model.load_model(str(model_path))
    return model


def predict_smiles(smiles: str, model_path: Path = None) -> PredictionResponse:
    model_path = model_path or (settings.MODELS_DIR / "xgboost_esol_latest.json")
    model = load_xgboost_model(model_path)

    canon = canonicalize_smiles(smiles)
    if not canon:
        raise ValueError(f"Invalid SMILES string: {smiles}")

    mol = parse_smiles(canon)
    descriptors = compute_molecular_descriptors(mol)
    fp = compute_morgan_fingerprint(mol, radius=2, n_bits=1024)

    # Reconstruct feature vector matching training schema
    extractor = FeatureExtractor(FeatureConfig())
    dummy_df = pd.DataFrame([{**descriptors, "fingerprint": "".join(map(str, fp)), "target": 0.0}])
    X, _, _ = extractor.extract(dummy_df)

    pred = float(model.predict(X)[0])

    return PredictionResponse(
        smiles=smiles,
        canonical_smiles=canon,
        predicted_value=round(pred, 4),
        unit="log mol/L",
        model_id=model_path.stem,
        descriptors=descriptors,
    )


def evaluate_dataset(model_path: Path, dataset_path: Path) -> Dict[str, Any]:
    model = load_xgboost_model(model_path)
    df = pd.read_csv(dataset_path, dtype={"fingerprint": str})

    splitter = DatasetSplitter()
    _, _, test_df = splitter.split(df)

    extractor = FeatureExtractor()
    X_test, y_test, _ = extractor.extract(test_df)

    y_pred = model.predict(X_test)
    metrics = compute_regression_metrics(y_test, y_pred)

    comparison = [
        {
            "compound_id": test_df.iloc[i]["compound_id"],
            "actual": round(float(y_test[i]), 3),
            "predicted": round(float(y_pred[i]), 3),
            "residual": round(float(y_pred[i] - y_test[i]), 3),
        }
        for i in range(len(test_df))
    ]

    return {
        "metrics": metrics,
        "sample_predictions": comparison,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate XGBoost Model")
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="models/xgboost_esol_latest.json",
        help="Path to XGBoost model artifact",
    )
    parser.add_argument(
        "--dataset",
        "-d",
        type=str,
        default="data/processed/esol_processed.csv",
        help="Dataset path for evaluation",
    )
    parser.add_argument("--smiles", "-s", type=str, default=None, help="SMILES to predict")

    args = parser.parse_args()

    model_path = Path(args.model)

    if args.smiles:
        res = predict_smiles(args.smiles, model_path)
        print("\n================ PREDICTION RESULT ================")
        print(f"Input SMILES:      {res.smiles}")
        print(f"Canonical SMILES:  {res.canonical_smiles}")
        print(f"Predicted Sol:     {res.predicted_value} {res.unit}")
        print(f"Molecular Weight:  {res.descriptors['molecular_weight']}")
        print(f"LogP:              {res.descriptors['logp']}")
        print("===================================================\n")
    else:
        results = evaluate_dataset(model_path, Path(args.dataset))
        print("\n================ EVALUATION METRICS ================")
        print(f"Test RMSE: {results['metrics']['rmse']}")
        print(f"Test MAE:  {results['metrics']['mae']}")
        print(f"Test R2:   {results['metrics']['r2']}")
        print("\nSample Test Predictions:")
        for sample in results["sample_predictions"][:5]:
            print(f"  ID: {sample['compound_id']} | Actual: {sample['actual']} | Pred: {sample['predicted']}")
        print("====================================================\n")


if __name__ == "__main__":
    main()
