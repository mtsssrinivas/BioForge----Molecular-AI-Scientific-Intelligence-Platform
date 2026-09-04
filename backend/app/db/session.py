"""
Database Session and Engine Management
Configures connection pooling and yield-based dependency injection for FastAPI.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings

from backend.app.core.logging import logger

# Configure connection pooling and dialect options
connect_args = {}
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
except Exception as exc:
    logger.error(
        f"Failed to create database engine with DATABASE_URL '{db_url}': {exc}. "
        "Falling back to local SQLite to ensure service boots."
    )
    fallback_url = f"sqlite:///{settings.BASE_DIR}/data/bioforge.db"
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency injection generator for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
