"""
BioForge Molecular Data Engineering & ETL Pipeline
Standardizes, validates, deduplicates, and generates RDKit descriptors and fingerprints.
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.utils.rdkit_utils import (
    parse_smiles,
    canonicalize_smiles,
    compute_molecular_descriptors,
    compute_morgan_fingerprint,
)
from backend.app.schemas.dataset import (
    PreprocessingConfig,
    DataQualityReport,
    FeatureStatistics,
    MalformedRecord,
)


class MolecularETLPipeline:
    """
    Production-grade ETL pipeline for molecular datasets.
    Validates, cleans, standardizes, generates physicochemical descriptors and fingerprints,
    and produces an audited data-quality report.
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig(random_seed=settings.RANDOM_SEED)

    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Strip whitespaces and lowercase column headers for consistent indexing."""
        df = df.copy()
        df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
        return df

    def run(
        self,
        input_csv_path: Path,
        dataset_name: str,
        smiles_column: str = "smiles",
        target_column: str = "target",
        id_column: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> Tuple[pd.DataFrame, DataQualityReport]:
        """
        Execute full ETL pipeline on target CSV file.
        """
        output_dir = output_dir or (settings.DATA_DIR / "processed")
        output_dir.mkdir(parents=True, exist_ok=True)

        if not input_csv_path.exists():
            raise FileNotFoundError(f"Dataset file not found at: {input_csv_path}")

        logger.info(f"Starting ETL for '{dataset_name}' from {input_csv_path}")
        raw_df = pd.read_csv(input_csv_path)
        total_records = len(raw_df)

        df = self.normalize_column_names(raw_df)
        smiles_col = smiles_column.strip().lower().replace(" ", "_").replace("-", "_")
        target_col = target_column.strip().lower().replace(" ", "_").replace("-", "_")
        id_col = id_column.strip().lower().replace(" ", "_").replace("-", "_") if id_column else None

        if smiles_col not in df.columns:
            raise ValueError(
                f"SMILES column '{smiles_column}' not found in dataset. Available columns: {list(df.columns)}"
            )

        if target_col not in df.columns:
            raise ValueError(
                f"Target column '{target_column}' not found in dataset. Available columns: {list(df.columns)}"
            )

        malformed_records: List[MalformedRecord] = []
        valid_rows: List[Dict[str, Any]] = []
        seen_canonical_smiles = set()
        duplicate_count = 0
        missing_target_count = 0
        invalid_molecule_count = 0

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            raw_smiles = row.get(smiles_col)
            raw_target = row.get(target_col)

            # 1. Missing SMILES check
            if pd.isna(raw_smiles) or not str(raw_smiles).strip():
                malformed_records.append(
                    MalformedRecord(row_index=idx, raw_data=row_dict, reason="Missing SMILES value")
                )
                invalid_molecule_count += 1
                continue

            # 2. Target validation (missing or non-numeric)
            if pd.isna(raw_target):
                malformed_records.append(
                    MalformedRecord(row_index=idx, raw_data=row_dict, reason="Missing target property value")
                )
                missing_target_count += 1
                continue

            try:
                numeric_target = float(raw_target)
            except (ValueError, TypeError):
                malformed_records.append(
                    MalformedRecord(row_index=idx, raw_data=row_dict, reason=f"Malformed non-numeric target: {raw_target}")
                )
                missing_target_count += 1
                continue

            # 3. RDKit Molecular parsing & canonicalization
            mol = parse_smiles(str(raw_smiles))
            if mol is None:
                malformed_records.append(
                    MalformedRecord(row_index=idx, raw_data=row_dict, reason=f"Invalid SMILES structure: {raw_smiles}")
                )
                invalid_molecule_count += 1
                continue

            canonical_smiles = canonicalize_smiles(str(raw_smiles))
            if not canonical_smiles:
                malformed_records.append(
                    MalformedRecord(row_index=idx, raw_data=row_dict, reason=f"Failed canonicalization for: {raw_smiles}")
                )
                invalid_molecule_count += 1
                continue

            # 4. Duplicate handling
            if self.config.remove_duplicates and canonical_smiles in seen_canonical_smiles:
                malformed_records.append(
                    MalformedRecord(row_index=idx, raw_data=row_dict, reason=f"Duplicate molecule: {canonical_smiles}")
                )
                duplicate_count += 1
                continue

            seen_canonical_smiles.add(canonical_smiles)

            # 5. Descriptor calculation
            try:
                descriptors = compute_molecular_descriptors(mol)
            except Exception as e:
                malformed_records.append(
                    MalformedRecord(row_index=idx, raw_data=row_dict, reason=f"Descriptor computation error: {str(e)}")
                )
                invalid_molecule_count += 1
                continue

            # 6. Morgan Fingerprint generation (stored as comma-separated or vector)
            fp_array = compute_morgan_fingerprint(
                mol, radius=self.config.fingerprint_radius, n_bits=self.config.fingerprint_bits
            )
            # Store fingerprint as bit string for clean CSV representation
            fp_bitstring = "".join(map(str, fp_array))

            compound_id = str(row[id_col]) if id_col and id_col in df.columns and pd.notna(row[id_col]) else f"{dataset_name.upper()}-{idx:05d}"

            record = {
                "compound_id": compound_id,
                "original_smiles": str(raw_smiles),
                "canonical_smiles": canonical_smiles,
                "target": numeric_target,
                **descriptors,
                "fingerprint": fp_bitstring,
            }
            valid_rows.append(record)

        processed_df = pd.DataFrame(valid_rows)

        # Compute feature statistics on processed dataset
        feature_stats: Dict[str, FeatureStatistics] = {}
        if not processed_df.empty:
            stat_cols = [
                "target",
                "molecular_weight",
                "logp",
                "tpsa",
                "h_bond_donors",
                "h_bond_acceptors",
                "rotatable_bonds",
                "heavy_atom_count",
                "ring_count",
            ]
            for col in stat_cols:
                if col in processed_df.columns:
                    feature_stats[col] = FeatureStatistics(
                        mean=float(processed_df[col].mean()),
                        std=float(processed_df[col].std()),
                        min=float(processed_df[col].min()),
                        max=float(processed_df[col].max()),
                        median=float(processed_df[col].median()),
                    )

        valid_count = len(processed_df)
        report = DataQualityReport(
            dataset_name=dataset_name,
            total_records=total_records,
            valid_molecules=valid_count,
            invalid_molecules=invalid_molecule_count,
            duplicate_records=duplicate_count,
            missing_targets=missing_target_count,
            processed_records=valid_count,
            feature_statistics=feature_stats,
            malformed_records=malformed_records,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save artifacts
        output_csv = output_dir / f"{dataset_name}_processed.csv"
        output_meta = output_dir / f"{dataset_name}_quality_report.json"

        processed_df.to_csv(output_csv, index=False)
        with open(output_meta, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        logger.info(
            f"ETL completed successfully: {valid_count}/{total_records} valid records saved to {output_csv}"
        )
        return processed_df, report


def main():
    parser = argparse.ArgumentParser(description="BioForge Molecular ETL Pipeline CLI")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input CSV file")
    parser.add_argument("--name", "-n", type=str, required=True, help="Dataset name identifier")
    parser.add_argument("--smiles-col", type=str, default="smiles", help="Name of SMILES column")
    parser.add_argument("--target-col", type=str, default="target", help="Name of target property column")
    parser.add_argument("--id-col", type=str, default=None, help="Name of compound identifier column")
    parser.add_argument("--output-dir", "-o", type=str, default=None, help="Output directory")

    args = parser.parse_args()

    pipeline = MolecularETLPipeline()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir) if args.output_dir else None

    df, report = pipeline.run(
        input_csv_path=input_path,
        dataset_name=args.name,
        smiles_column=args.smiles_col,
        target_column=args.target_col,
        id_column=args.id_col,
        output_dir=output_dir,
    )

    print(f"\n================ BIOFORGE ETL REPORT ================")
    print(f"Dataset Name:       {report.dataset_name}")
    print(f"Total Records:      {report.total_records}")
    print(f"Valid Processed:    {report.processed_records}")
    print(f"Invalid Molecules:  {report.invalid_molecules}")
    print(f"Duplicate Records:  {report.duplicate_records}")
    print(f"Missing Targets:    {report.missing_targets}")
    print(f"=====================================================")


if __name__ == "__main__":
    main()
