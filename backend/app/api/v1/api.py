"""
API Router V1 Aggregator
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    molecules,
    predictions,
    models,
    experiments,
    literature,
    rag,
    jobs,
)

api_router = APIRouter()

# Attach endpoint groups
api_router.include_router(health.router)
api_router.include_router(molecules.router)
api_router.include_router(predictions.router)
api_router.include_router(models.router)
api_router.include_router(experiments.router)
api_router.include_router(literature.router)
api_router.include_router(rag.router)
api_router.include_router(jobs.router)
