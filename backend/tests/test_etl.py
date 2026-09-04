"""
Unit tests for Molecular Data Engineering & ETL Pipeline (Phase 1)
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from backend.app.utils.rdkit_utils import (
    parse_smiles,
    canonicalize_smiles,
    compute_molecular_descriptors,
    compute_morgan_fingerprint,
    smiles_to_svg,
)
from backend.app.services.etl import MolecularETLPipeline
from backend.app.schemas.dataset import PreprocessingConfig


def test_valid_smiles_parsing():
    smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
    mol = parse_smiles(smiles)
    assert mol is not None
    canon = canonicalize_smiles(smiles)
    assert canon is not None
    assert isinstance(canon, str)


def test_invalid_smiles_handling():
    invalid_smiles = "NOT_A_SMILES_STRING!@#$%"
    mol = parse_smiles(invalid_smiles)
    assert mol is None
    canon = canonicalize_smiles(invalid_smiles)
    assert canon is None


def test_descriptor_generation():
    smiles = "CCO"  # Ethanol
    mol = parse_smiles(smiles)
    assert mol is not None
    descriptors = compute_molecular_descriptors(mol)

    assert "molecular_weight" in descriptors
    assert "logp" in descriptors
    assert "tpsa" in descriptors
    assert "h_bond_donors" in descriptors
    assert "h_bond_acceptors" in descriptors
    assert "rotatable_bonds" in descriptors

    assert 45.0 < descriptors["molecular_weight"] < 47.0
    assert descriptors["h_bond_donors"] == 1
    assert descriptors["h_bond_acceptors"] == 1


def test_fingerprint_generation():
    smiles = "c1ccccc1"  # Benzene
    mol = parse_smiles(smiles)
    assert mol is not None
    fp = compute_morgan_fingerprint(mol, radius=2, n_bits=1024)
    assert isinstance(fp, np.ndarray)
    assert len(fp) == 1024
    assert np.sum(fp) > 0


def test_svg_generation():
    smiles = "c1ccccc1"
    svg = smiles_to_svg(smiles)
    assert svg is not None
    assert "<svg" in svg
    assert "</svg>" in svg


def test_etl_pipeline_with_dev_fixture(tmp_path):
    dev_fixture_path = Path("data/raw/dev_fixture.csv")
    assert dev_fixture_path.exists()

    pipeline = MolecularETLPipeline(config=PreprocessingConfig(remove_duplicates=True))
    processed_df, report = pipeline.run(
        input_csv_path=dev_fixture_path,
        dataset_name="test_fixture",
        smiles_column="smiles",
        target_column="solubility",
        id_column="compound_id",
        output_dir=tmp_path,
    )

    # In dev_fixture.csv:
    # DEV-01: Valid
    # DEV-02: Invalid SMILES
    # DEV-03: Valid
    # DEV-04: Missing target
    # DEV-05: Duplicate of DEV-01
    # DEV-06: Missing SMILES
    # DEV-07: Malformed NaN target
    # DEV-08: Valid (Benzene)
    assert report.total_records == 8
    assert report.invalid_molecules == 2  # DEV-02 invalid, DEV-06 missing SMILES
    assert report.missing_targets == 2    # DEV-04 empty, DEV-07 non-numeric
    assert report.duplicate_records == 1  # DEV-05
    assert report.processed_records == 3  # DEV-01, DEV-03, DEV-08
    assert len(processed_df) == 3

    # Check output files exist
    assert (tmp_path / "test_fixture_processed.csv").exists()
    assert (tmp_path / "test_fixture_quality_report.json").exists()


def test_etl_delaney_dataset():
    esol_path = Path("data/raw/esol_raw.csv")
    assert esol_path.exists()

    pipeline = MolecularETLPipeline()
    processed_df, report = pipeline.run(
        input_csv_path=esol_path,
        dataset_name="esol",
        smiles_column="smiles",
        target_column="measured log solubility in mols per litre",
        id_column="Compound ID",
    )

    assert report.total_records == 50
    assert report.processed_records == 50
    assert report.invalid_molecules == 0
    assert report.duplicate_records == 0
    assert "target" in report.feature_statistics
    assert "molecular_weight" in report.feature_statistics
