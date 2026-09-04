"""
Database Schema Initialization and Data Ingestion Utility
"""

from pathlib import Path
import pandas as pd
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.base import Base
from backend.app.db.session import engine, SessionLocal
import backend.app.db.models
from backend.app.services.repository import MoleculeRepository, ExperimentRepository


def init_db(populate_from_processed: bool = True):
    """Initialize database tables and optionally populate from processed datasets."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    if populate_from_processed:
        processed_esol = settings.DATA_DIR / "processed" / "esol_processed.csv"
        if processed_esol.exists():
            db = SessionLocal()
            try:
                repo = MoleculeRepository(db)
                dataset = repo.get_or_create_dataset(
                    name="ESOL",
                    description="Delaney aqueous solubility benchmark dataset (LogS)",
                    total_records=50,
                )

                df = pd.read_csv(processed_esol, dtype={"fingerprint": str})
                inserted = 0
                for _, row in df.iterrows():
                    existing = repo.get_molecule_by_smiles(row["canonical_smiles"])
                    if not existing:
                        repo.create_molecule(
                            dataset_id=dataset.id,
                            compound_id=str(row["compound_id"]),
                            canonical_smiles=str(row["canonical_smiles"]),
                            original_smiles=str(row["original_smiles"]),
                            target_value=float(row["target"]),
                            descriptors={
                                "molecular_weight": float(row["molecular_weight"]),
                                "logp": float(row["logp"]),
                                "tpsa": float(row["tpsa"]),
                                "h_bond_donors": int(row["h_bond_donors"]),
                                "h_bond_acceptors": int(row["h_bond_acceptors"]),
                                "rotatable_bonds": int(row["rotatable_bonds"]),
                            },
                            fingerprint=str(row["fingerprint"]),
                        )
                        inserted += 1

                logger.info(f"Database populated with {inserted} molecules from {processed_esol.name}")
            finally:
                db.close()


if __name__ == "__main__":
    init_db()
