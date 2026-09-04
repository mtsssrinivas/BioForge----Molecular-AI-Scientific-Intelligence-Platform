"""
Dataset Schemas and Quality Reporting Models
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PreprocessingConfig(BaseModel):
    fingerprint_radius: int = Field(default=2, description="Morgan fingerprint radius")
    fingerprint_bits: int = Field(default=1024, description="Fingerprint bit length")
    remove_duplicates: bool = Field(default=True, description="Whether to deduplicate by canonical SMILES")
    random_seed: int = Field(default=42, description="Deterministic seed")


class FeatureStatistics(BaseModel):
    mean: float
    std: float
    min: float
    max: float
    median: float


class MalformedRecord(BaseModel):
    row_index: int
    raw_data: Dict[str, Any]
    reason: str


class DataQualityReport(BaseModel):
    dataset_name: str
    total_records: int
    valid_molecules: int
    invalid_molecules: int
    duplicate_records: int
    missing_targets: int
    processed_records: int
    feature_statistics: Dict[str, FeatureStatistics]
    malformed_records: List[MalformedRecord] = Field(default_factory=list)
    created_at: str
