"""
Feature Extraction Module for Classical ML
Extracts RDKit physicochemical descriptors and Morgan bit fingerprints from processed records.
"""

from typing import Tuple, List
import numpy as np
import pandas as pd
from backend.app.schemas.ml import FeatureConfig

DESCRIPTOR_COLUMNS = [
    "molecular_weight",
    "logp",
    "tpsa",
    "h_bond_donors",
    "h_bond_acceptors",
    "rotatable_bonds",
    "heavy_atom_count",
    "ring_count",
]


class FeatureExtractor:
    """Constructs feature matrix X and target vector y from processed molecular DataFrame."""

    def __init__(self, config: FeatureConfig = None):
        self.config = config or FeatureConfig()
        self.descriptor_cols = DESCRIPTOR_COLUMNS

    def extract(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        feature_parts = []
        feature_names = []

        # 1. RDKit Descriptors
        if self.config.use_descriptors:
            desc_values = df[self.descriptor_cols].to_numpy(dtype=np.float32)
            feature_parts.append(desc_values)
            feature_names.extend(self.descriptor_cols)

        # 2. Morgan Fingerprints
        if self.config.use_fingerprints:
            fp_strings = df["fingerprint"].tolist()
            fp_matrix = np.array(
                [[int(bit) for bit in s[: self.config.fingerprint_bits]] for s in fp_strings],
                dtype=np.float32,
            )
            feature_parts.append(fp_matrix)
            feature_names.extend([f"fp_bit_{i}" for i in range(self.config.fingerprint_bits)])

        if not feature_parts:
            raise ValueError("Feature configuration has both descriptors and fingerprints disabled")

        X = np.hstack(feature_parts)
        y = df["target"].to_numpy(dtype=np.float32)

        return X, y, feature_names
