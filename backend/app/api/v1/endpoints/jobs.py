"""
Asynchronous Job Management and Server-Sent Events (SSE) Streaming
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from backend.app.schemas.job import JobResponse
from backend.app.services.job_service import job_manager

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/prediction", response_model=JobResponse)
async def submit_prediction_job(
    smiles: str = Query(..., description="Molecular SMILES to predict"),
    model_type: str = Query("xgboost", description="Model type (xgboost or gnn)"),
):
    job_id = job_manager.create_prediction_job(smiles=smiles, model_type=model_type)
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=500, detail="Failed to initialize job")
    return job


@router.get("", response_model=List[JobResponse])
def list_jobs():
    return job_manager.list_jobs()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str):
    """
    Server-Sent Events (SSE) streaming endpoint delivering live stage updates.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return EventSourceResponse(
        job_manager.subscribe(job_id),
        media_type="text/event-stream",
    )
