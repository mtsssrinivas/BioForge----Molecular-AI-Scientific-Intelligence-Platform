"""
Pytest global fixtures for BioForge
"""

import os
import sys
from pathlib import Path
import pytest

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure backend directory is also on sys.path
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope="session")
def sample_smiles_list():
    return [
        {"compound_id": "MOL-001", "smiles": "CC(=O)Oc1ccccc1C(=O)O", "solubility": -1.31},  # Aspirin
        {"compound_id": "MOL-002", "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O", "solubility": -2.85},  # Ibuprofen
        {"compound_id": "MOL-003", "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "solubility": -1.04},  # Caffeine
        {"compound_id": "MOL-004", "smiles": "c1ccccc1", "solubility": -2.13},  # Benzene
        {"compound_id": "MOL-005", "smiles": "CCO", "solubility": 0.50},  # Ethanol
    ]


@pytest.fixture(scope="session")
def invalid_smiles():
    return "InvalidSMILES_12345%&"
