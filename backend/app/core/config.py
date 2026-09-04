"""
BioForge Core Configuration
Centralized settings management powered by Pydantic Settings.
Reads from environment variables and .env file safely without hardcoded secrets.
"""

from typing import List, Union
from pathlib import Path
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the BioForge project
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "BioForge"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    RANDOM_SEED: int = 42

    # API
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/bioforge.db"
    POSTGRES_USER: str = "bioforge_user"
    POSTGRES_PASSWORD: str = "bioforge_secure_password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "bioforge"

    # Redis & Asynchronous Workers
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Literature & Vector Search
    EMBEDDING_DIMENSION: int = 384
    LLM_PROVIDER: str = "mock"  # mock, openai, anthropic
    OPENAI_API_KEY: str = ""

    # Paths
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
    EXPERIMENTS_DIR: Path = BASE_DIR / "experiments"

    @field_validator("PORT", mode="before")
    @classmethod
    def assemble_port(cls, v: Union[int, str, None]) -> int:
        if v is None:
            return 8000
        if isinstance(v, str):
            try:
                return int(v.strip())
            except ValueError:
                return 8000
        return int(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        if not v:
            return ["*"]
        if isinstance(v, str):
            v_str = v.strip()
            if not v_str:
                return ["*"]
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except Exception:
                    pass
            return [i.strip() for i in v_str.split(",") if i.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v]
        return ["*"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: Union[str, None]) -> str:
        if not v or not str(v).strip():
            return f"sqlite:///{BASE_DIR}/data/bioforge.db"
        v_str = str(v).strip()
        # Render and Heroku inject postgres:// which SQLAlchemy 2.0 rejects
        if v_str.startswith("postgres://"):
            return v_str.replace("postgres://", "postgresql+psycopg2://", 1)
        elif v_str.startswith("postgresql://") and "+psycopg2" not in v_str and "+asyncpg" not in v_str:
            return v_str.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v_str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

# Ensure standard runtime folders exist
try:
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    (settings.DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (settings.DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    (settings.DATA_DIR / "external").mkdir(parents=True, exist_ok=True)
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    settings.EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
