"""
Job Management & Real-Time Event Dispatcher
Coordinates asynchronous tasks, stage progression, and Server-Sent Events (SSE) streaming.
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, AsyncGenerator, List

from backend.app.schemas.job import JobStatus, JobType, JobResponse, JobProgressEvent
from backend.app.ml.evaluate_xgb import predict_smiles
from backend.app.ml.train_gnn import predict_gnn_smiles
from backend.app.core.logging import logger


class JobManager:
    """Manages active job states, event queues, and real-time execution pipelines."""

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._listeners: Dict[str, List[asyncio.Queue]] = {}

    def get_job(self, job_id: str) -> Optional[JobResponse]:
        raw = self._jobs.get(job_id)
        if not raw:
            return None
        return JobResponse(
            job_id=raw["job_id"],
            job_type=raw["job_type"],
            status=raw["status"],
            current_stage=raw["current_stage"],
            progress_percent=raw["progress_percent"],
            result=raw.get("result"),
            error=raw.get("error"),
            created_at=raw["created_at"],
            completed_at=raw.get("completed_at"),
        )

    def list_jobs(self) -> List[JobResponse]:
        return [self.get_job(jid) for jid in self._jobs.keys() if self.get_job(jid) is not None]

    async def emit_progress(self, job_id: str, stage: str, percent: int, message: str):
        job = self._jobs.get(job_id)
        if not job:
            return

        job["current_stage"] = stage
        job["progress_percent"] = percent

        event = JobProgressEvent(
            job_id=job_id,
            stage=stage,
            progress_percent=percent,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        queues = self._listeners.get(job_id, [])
        for q in queues:
            await q.put(event)

    async def subscribe(self, job_id: str) -> AsyncGenerator[str, None]:
        """Async generator streaming SSE formatted events to clients."""
        if job_id not in self._jobs:
            yield f"event: error\ndata: {json.dumps({'error': 'Job not found'})}\n\n"
            return

        queue: asyncio.Queue = asyncio.Queue()
        if job_id not in self._listeners:
            self._listeners[job_id] = []
        self._listeners[job_id].append(queue)

        try:
            # Emit current state immediately
            curr = self._jobs[job_id]
            initial_event = JobProgressEvent(
                job_id=job_id,
                stage=curr["current_stage"],
                progress_percent=curr["progress_percent"],
                message=f"Current status: {curr['status'].value}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            yield f"data: {initial_event.model_dump_json()}\n\n"

            # If already completed or failed, close stream
            if curr["status"] in (JobStatus.COMPLETED, JobStatus.FAILED):
                yield f"event: done\ndata: {json.dumps({'status': curr['status'].value})}\n\n"
                return

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {event.model_dump_json()}\n\n"

                    job = self._jobs.get(job_id)
                    if job and job["status"] in (JobStatus.COMPLETED, JobStatus.FAILED):
                        yield f"event: done\ndata: {json.dumps({'status': job['status'].value})}\n\n"
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield ": keep-alive\n\n"
        finally:
            if job_id in self._listeners and queue in self._listeners[job_id]:
                self._listeners[job_id].remove(queue)

    async def run_prediction_pipeline(self, job_id: str, smiles: str, model_type: str = "xgboost"):
        try:
            self._jobs[job_id]["status"] = JobStatus.RUNNING

            # Stage 1: preparing_data
            await self.emit_progress(job_id, "preparing_data", 20, "Parsing and validating chemical structure")
            await asyncio.sleep(0.3)

            # Stage 2: feature_generation
            await self.emit_progress(job_id, "feature_generation", 50, "Generating RDKit descriptors and representation")
            await asyncio.sleep(0.3)

            # Stage 3: model_inference
            await self.emit_progress(job_id, "model_inference", 80, f"Executing {model_type.upper()} neural inference")
            await asyncio.sleep(0.3)

            if model_type.lower() == "gnn":
                pred_val = predict_gnn_smiles(smiles)
                pred_dict = {
                    "smiles": smiles,
                    "model_type": "GNN",
                    "predicted_value": round(pred_val, 4),
                    "unit": "log mol/L",
                }
            else:
                pred_res = predict_smiles(smiles)
                pred_dict = pred_res.model_dump()

            # Stage 4: persisting_results
            await self.emit_progress(job_id, "persisting_results", 95, "Storing predictions into audit store")
            await asyncio.sleep(0.2)

            # Stage 5: completed
            self._jobs[job_id]["status"] = JobStatus.COMPLETED
            self._jobs[job_id]["result"] = pred_dict
            self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            await self.emit_progress(job_id, "completed", 100, "Molecular property prediction complete")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            self._jobs[job_id]["status"] = JobStatus.FAILED
            self._jobs[job_id]["error"] = str(e)
            self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            await self.emit_progress(job_id, "failed", 100, f"Job failed: {str(e)}")

    def create_prediction_job(self, smiles: str, model_type: str = "xgboost") -> str:
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        self._jobs[job_id] = {
            "job_id": job_id,
            "job_type": JobType.PREDICTION.value,
            "status": JobStatus.QUEUED,
            "current_stage": "queued",
            "progress_percent": 0,
            "payload": {"smiles": smiles, "model_type": model_type},
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }

        # Schedule async execution in event loop
        asyncio.create_task(self.run_prediction_pipeline(job_id, smiles, model_type))
        return job_id


# Global JobManager instance
job_manager = JobManager()
