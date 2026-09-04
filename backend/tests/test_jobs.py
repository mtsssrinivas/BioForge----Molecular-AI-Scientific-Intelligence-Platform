"""
Unit tests for Job Execution and SSE Progress Streaming (Phase 8 & 9)
"""

import pytest
import asyncio
from backend.app.services.job_service import job_manager
from backend.app.schemas.job import JobStatus


def test_job_lifecycle_and_progress_events():
    async def _test():
        aspirin = "CC(=O)Oc1ccccc1C(=O)O"
        job_id = job_manager.create_prediction_job(smiles=aspirin, model_type="xgboost")

        assert job_id.startswith("JOB-")
        initial_job = job_manager.get_job(job_id)
        assert initial_job is not None
        assert initial_job.status in (JobStatus.QUEUED, JobStatus.RUNNING)

        # Collect SSE events from generator
        events = []
        async for event_str in job_manager.subscribe(job_id):
            events.append(event_str)
            if "done" in event_str or "completed" in event_str:
                break

        assert len(events) >= 2
        final_job = job_manager.get_job(job_id)
        assert final_job.status == JobStatus.COMPLETED
        assert final_job.result is not None
        assert "predicted_value" in final_job.result

    asyncio.run(_test())


def test_invalid_job_id_events():
    async def _test():
        events = []
        async for event_str in job_manager.subscribe("JOB-INVALID-99999"):
            events.append(event_str)

        assert len(events) == 1
        assert "error" in events[0]
        assert "Job not found" in events[0]

    asyncio.run(_test())


def test_job_failure_handling():
    async def _test():
        invalid_smiles = "NOT_A_MOLECULE!@#"
        job_id = job_manager.create_prediction_job(smiles=invalid_smiles, model_type="xgboost")

        async for _ in job_manager.subscribe(job_id):
            pass

        failed_job = job_manager.get_job(job_id)
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.error is not None

    asyncio.run(_test())
