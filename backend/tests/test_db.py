"""
Unit tests for Database Persistence Layer (Phase 4)
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base
from backend.app.db.models import DatasetRecord, MoleculeRecord, MLModelRecord, ExperimentRecord
from backend.app.services.repository import MoleculeRepository, ExperimentRepository, PredictionRepository


@pytest.fixture
def db_session():
    # In-memory SQLite for isolated high-speed database testing
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_dataset_and_molecule_persistence(db_session):
    repo = MoleculeRepository(db_session)
    dataset = repo.get_or_create_dataset(name="ESOL_TEST", description="Test solubility set")
    assert dataset.id.startswith("DS-")

    aspirin_smiles = "CC(=O)Oc1ccccc1C(=O)O"
    mol = repo.create_molecule(
        dataset_id=dataset.id,
        compound_id="MOL-01",
        canonical_smiles=aspirin_smiles,
        original_smiles=aspirin_smiles,
        target_value=-1.31,
        descriptors={"molecular_weight": 180.16, "logp": 1.31, "tpsa": 63.6},
    )

    assert mol.id.startswith("MOL-")
    assert mol.canonical_smiles == aspirin_smiles
    assert mol.dataset.name == "ESOL_TEST"

    # Query back
    fetched = repo.get_molecule_by_id(mol.id)
    assert fetched is not None
    assert fetched.compound_id == "MOL-01"


def test_experiment_and_evaluation_persistence(db_session):
    mol_repo = MoleculeRepository(db_session)
    dataset = mol_repo.get_or_create_dataset(name="ESOL_BENCH")

    exp_repo = ExperimentRepository(db_session)
    model = exp_repo.get_or_create_model(
        model_id="xgb-model-01",
        name="XGBoost Baseline",
        model_type="xgboost",
        artifact_path="models/test.json",
    )
    assert model.id == "xgb-model-01"

    exp = exp_repo.create_experiment(
        experiment_id="EXP-TEST-001",
        name="Solubility Test Run",
        dataset_id=dataset.id,
        model_id=model.id,
        hyperparameters={"max_depth": 4},
        feature_config={"use_descriptors": True},
        metrics_val={"rmse": 0.55},
        metrics_test={"rmse": 0.52, "r2": 0.65},
        duration=1.2,
    )

    assert exp.id == "EXP-TEST-001"
    assert len(exp.evaluations) == 2  # rmse and r2 records created
    assert exp.dataset.name == "ESOL_BENCH"
    assert exp.model.name == "XGBoost Baseline"


def test_prediction_persistence(db_session):
    pred_repo = PredictionRepository(db_session)
    exp_repo = ExperimentRepository(db_session)

    model = exp_repo.get_or_create_model(
        model_id="test-model",
        name="Model",
        model_type="xgboost",
        artifact_path="path",
    )

    pred = pred_repo.record_prediction(
        model_id=model.id,
        input_smiles="CCO",
        canonical_smiles="CCO",
        predicted_value=0.48,
        inference_time_ms=5.2,
    )

    assert pred.id.startswith("PRED-")
    assert pred.predicted_value == 0.48
    retrieved = pred_repo.get_prediction(pred.id)
    assert retrieved is not None
    assert retrieved.canonical_smiles == "CCO"
