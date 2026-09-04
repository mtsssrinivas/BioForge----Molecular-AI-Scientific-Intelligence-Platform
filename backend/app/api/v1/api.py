"""
API Router V1 Aggregator
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import health
from backend.app.api.v1.endpoints import molecules
from backend.app.api.v1.endpoints import predictions
from backend.app.api.v1.endpoints import models
from backend.app.api.v1.endpoints import experiments
from backend.app.api.v1.endpoints import literature
from backend.app.api.v1.endpoints import rag
from backend.app.api.v1.endpoints import jobs

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
