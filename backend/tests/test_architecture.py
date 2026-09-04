"""
Architectural and environment baseline tests for BioForge.
"""

from pathlib import Path
from backend.app.core.config import settings


def test_directory_structure():
    assert settings.DATA_DIR.exists()
    assert (settings.DATA_DIR / "raw").exists()
    assert (settings.DATA_DIR / "processed").exists()
    assert settings.MODELS_DIR.exists()
    assert settings.EXPERIMENTS_DIR.exists()


def test_settings_loaded():
    assert settings.PROJECT_NAME == "BioForge"
    assert settings.RANDOM_SEED == 42
    assert settings.EMBEDDING_DIMENSION == 384
