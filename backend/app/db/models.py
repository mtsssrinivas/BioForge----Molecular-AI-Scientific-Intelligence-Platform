"""
Relational Database Models for BioForge
Normalized schema for molecules, datasets, experiments, models, evaluations, predictions, and literature.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.app.db.base import Base


class DatasetRecord(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    task_type: Mapped[str] = mapped_column(String(64), default="regression")
    target_property: Mapped[str] = mapped_column(String(128), default="solubility")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    molecules = relationship("MoleculeRecord", back_populates="dataset", cascade="all, delete-orphan")
    experiments = relationship("ExperimentRecord", back_populates="dataset")


class MoleculeRecord(Base):
    __tablename__ = "molecules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id"), index=True, nullable=False)
    compound_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    canonical_smiles: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    original_smiles: Mapped[str] = mapped_column(Text, nullable=False)
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Core physicochemical descriptors
    molecular_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    logp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tpsa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    h_bond_donors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    h_bond_acceptors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rotatable_bonds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    fingerprint_bits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    dataset = relationship("DatasetRecord", back_populates="molecules")
    predictions = relationship("PredictionRecord", back_populates="molecule")

    __table_args__ = (
        Index("idx_molecules_dataset_canonical", "dataset_id", "canonical_smiles"),
    )


class MLModelRecord(Base):
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # "xgboost" or "gnn"
    framework: Mapped[str] = mapped_column(String(64), default="xgboost")
    version: Mapped[str] = mapped_column(String(32), default="v1.0")
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    experiments = relationship("ExperimentRecord", back_populates="model")
    predictions = relationship("PredictionRecord", back_populates="model")


class ExperimentRecord(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id"), index=True, nullable=False)
    model_id: Mapped[str] = mapped_column(String(64), ForeignKey("ml_models.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="completed")  # queued, running, completed, failed
    training_duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    hyperparameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    feature_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    metrics_val: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    metrics_test: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    dataset = relationship("DatasetRecord", back_populates="experiments")
    model = relationship("MLModelRecord", back_populates="experiments")
    evaluations = relationship("EvaluationRecord", back_populates="experiment")


class EvaluationRecord(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    experiment_id: Mapped[str] = mapped_column(String(64), ForeignKey("experiments.id"), index=True, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    split_name: Mapped[str] = mapped_column(String(32), default="test")  # train, val, test
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    experiment = relationship("ExperimentRecord", back_populates="evaluations")


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    molecule_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("molecules.id"), nullable=True)
    model_id: Mapped[str] = mapped_column(String(64), ForeignKey("ml_models.id"), index=True, nullable=False)
    input_smiles: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_smiles: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="log mol/L")
    inference_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    molecule = relationship("MoleculeRecord", back_populates="predictions")
    model = relationship("MLModelRecord", back_populates="predictions")


class LiteratureDocument(Base):
    __tablename__ = "literature_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    authors: Mapped[str] = mapped_column(String(256), default="")
    source: Mapped[str] = mapped_column(String(128), default="PubMed")  # e.g., PubMed, Journal of Med Chem
    publication_year: Mapped[int] = mapped_column(Integer, default=2023)
    doi: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    abstract: Mapped[Text] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    chunks = relationship("LiteratureChunk", back_populates="document", cascade="all, delete-orphan")


class LiteratureChunk(Base):
    __tablename__ = "literature_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    document_id: Mapped[str] = mapped_column(String(64), ForeignKey("literature_documents.id"), index=True, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_json: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)  # JSON vector or pgvector
    citation_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    document = relationship("LiteratureDocument", back_populates="chunks")
