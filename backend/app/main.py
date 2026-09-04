"""
BioForge Backend Application Server
Production FastAPI service with CORS, lifespan initialization, structured routing, and error handling.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.api.v1.api import api_router
from backend.app.db.init_db import init_db
from backend.app.services.literature_service import LiteratureService


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")

    # 1. Initialize DB schema and seed baseline dataset
    try:
        init_db(populate_from_processed=True)
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    # 2. Ingest curated scientific literature for RAG
    try:
        lit_service = LiteratureService()
        fixture_path = settings.DATA_DIR / "raw" / "scientific_literature.json"
        if fixture_path.exists():
            count = lit_service.ingest_fixture_file(fixture_path)
            logger.info(f"Loaded {count} literature documents into vector store")
    except Exception as e:
        logger.warning(f"Literature loading warning: {e}")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-Grade Molecular AI & Scientific Intelligence Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Direct root health check
@app.get("/health", tags=["Health"])
def root_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }

# Mount API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
