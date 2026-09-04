"""
BioForge Service Layer Repositories
Clean data-access abstraction layer isolating database operations from route handlers.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from backend.app.db.models import (
    DatasetRecord,
    MoleculeRecord,
    MLModelRecord,
    ExperimentRecord,
    EvaluationRecord,
    PredictionRecord,
)


class MoleculeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_dataset(
        self, name: str, description: str = "", total_records: int = 0
    ) -> DatasetRecord:
        stmt = select(DatasetRecord).where(DatasetRecord.name == name)
        dataset = self.db.scalars(stmt).first()
        if not dataset:
            dataset = DatasetRecord(
                id=f"DS-{uuid.uuid4().hex[:8].upper()}",
                name=name,
                description=description,
                total_records=total_records,
            )
            self.db.add(dataset)
            self.db.commit()
            self.db.refresh(dataset)
        return dataset

    def create_molecule(
        self,
        dataset_id: str,
        compound_id: str,
        canonical_smiles: str,
        original_smiles: str,
        target_value: Optional[float] = None,
        descriptors: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[str] = None,
    ) -> MoleculeRecord:
        mol = MoleculeRecord(
            id=f"MOL-{uuid.uuid4().hex[:10].upper()}",
            dataset_id=dataset_id,
            compound_id=compound_id,
            canonical_smiles=canonical_smiles,
            original_smiles=original_smiles,
            target_value=target_value,
            molecular_weight=descriptors.get("molecular_weight") if descriptors else None,
            logp=descriptors.get("logp") if descriptors else None,
            tpsa=descriptors.get("tpsa") if descriptors else None,
            h_bond_donors=descriptors.get("h_bond_donors") if descriptors else None,
            h_bond_acceptors=descriptors.get("h_bond_acceptors") if descriptors else None,
            rotatable_bonds=descriptors.get("rotatable_bonds") if descriptors else None,
            fingerprint_bits=fingerprint,
        )
        self.db.add(mol)
        self.db.commit()
        self.db.refresh(mol)
        return mol

    def list_molecules(self, skip: int = 0, limit: int = 50) -> List[MoleculeRecord]:
        stmt = select(MoleculeRecord).order_by(MoleculeRecord.compound_id).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_molecule_by_id(self, molecule_id: str) -> Optional[MoleculeRecord]:
        return self.db.get(MoleculeRecord, molecule_id)

    def get_molecule_by_smiles(self, canonical_smiles: str) -> Optional[MoleculeRecord]:
        stmt = select(MoleculeRecord).where(MoleculeRecord.canonical_smiles == canonical_smiles)
        return self.db.scalars(stmt).first()


class ExperimentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_model(
        self,
        model_id: str,
        name: str,
        model_type: str,
        artifact_path: str,
        framework: str = "scikit-learn/xgboost",
    ) -> MLModelRecord:
        model = self.db.get(MLModelRecord, model_id)
        if not model:
            model = MLModelRecord(
                id=model_id,
                name=name,
                model_type=model_type,
                artifact_path=artifact_path,
                framework=framework,
            )
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
        return model

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        dataset_id: str,
        model_id: str,
        hyperparameters: Dict[str, Any],
        feature_config: Dict[str, Any],
        metrics_val: Dict[str, float],
        metrics_test: Dict[str, float],
        duration: float,
    ) -> ExperimentRecord:
        exp = ExperimentRecord(
            id=experiment_id,
            name=name,
            dataset_id=dataset_id,
            model_id=model_id,
            hyperparameters=hyperparameters,
            feature_config=feature_config,
            metrics_val=metrics_val,
            metrics_test=metrics_test,
            training_duration_seconds=duration,
        )
        self.db.add(exp)

        for metric_name, val in metrics_test.items():
            eval_record = EvaluationRecord(
                id=f"EVAL-{uuid.uuid4().hex[:8].upper()}",
                experiment_id=experiment_id,
                metric_name=metric_name,
                metric_value=float(val),
                split_name="test",
            )
            self.db.add(eval_record)

        self.db.commit()
        self.db.refresh(exp)
        return exp

    def list_experiments(self, skip: int = 0, limit: int = 50) -> List[ExperimentRecord]:
        stmt = select(ExperimentRecord).order_by(desc(ExperimentRecord.created_at)).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_experiment(self, exp_id: str) -> Optional[ExperimentRecord]:
        return self.db.get(ExperimentRecord, exp_id)


class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_prediction(
        self,
        model_id: str,
        input_smiles: str,
        canonical_smiles: str,
        predicted_value: float,
        unit: str = "log mol/L",
        inference_time_ms: float = 0.0,
        molecule_id: Optional[str] = None,
    ) -> PredictionRecord:
        pred = PredictionRecord(
            id=f"PRED-{uuid.uuid4().hex[:10].upper()}",
            molecule_id=molecule_id,
            model_id=model_id,
            input_smiles=input_smiles,
            canonical_smiles=canonical_smiles,
            predicted_value=predicted_value,
            unit=unit,
            inference_time_ms=inference_time_ms,
        )
        self.db.add(pred)
        self.db.commit()
        self.db.refresh(pred)
        return pred

    def get_prediction(self, pred_id: str) -> Optional[PredictionRecord]:
        return self.db.get(PredictionRecord, pred_id)
