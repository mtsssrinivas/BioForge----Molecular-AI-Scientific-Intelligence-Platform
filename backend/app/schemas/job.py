"""
Schemas for Asynchronous Jobs and Server-Sent Events (SSE)
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    PREDICTION = "prediction"
    MODEL_TRAINING = "model_training"
    LITERATURE_INGEST = "literature_ingest"


class JobCreateRequest(BaseModel):
    job_type: JobType = JobType.PREDICTION
    payload: Dict[str, Any] = Field(default_factory=dict)


class JobProgressEvent(BaseModel):
    job_id: str
    stage: str
    progress_percent: int
    message: str
    timestamp: str


class JobResponse(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    current_stage: str
    progress_percent: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
