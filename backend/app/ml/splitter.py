"""
Dataset Splitting Module
Provides reproducible, leakage-free train/val/test splits with explicit seeds and tracking.
"""

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from backend.app.schemas.ml import SplitConfig


class DatasetSplitter:
    """Handles deterministic dataset partitioning into train, validation, and test sets."""

    def __init__(self, config: SplitConfig = None):
        self.config = config or SplitConfig()

    def split(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Partition dataframe into (train_df, val_df, test_df) deterministically.
        """
        n = len(df)
        if n < 3:
            raise ValueError(f"Dataset too small ({n} records) for 3-way split")

        total = self.config.train_ratio + self.config.val_ratio + self.config.test_ratio
        if not np.isclose(total, 1.0):
            raise ValueError(f"Split ratios must sum to 1.0 (got {total})")

        rng = np.random.RandomState(self.config.random_seed)
        shuffled_indices = rng.permutation(n)

        n_train = int(n * self.config.train_ratio)
        n_val = int(n * self.config.val_ratio)

        train_idx = shuffled_indices[:n_train]
        val_idx = shuffled_indices[n_train : n_train + n_val]
        test_idx = shuffled_indices[n_train + n_val :]

        train_df = df.iloc[train_idx].copy().reset_index(drop=True)
        val_df = df.iloc[val_idx].copy().reset_index(drop=True)
        test_df = df.iloc[test_idx].copy().reset_index(drop=True)

        return train_df, val_df, test_df
