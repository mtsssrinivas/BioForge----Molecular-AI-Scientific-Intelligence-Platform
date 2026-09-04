"""
Scientific literature endpoints
"""

from fastapi import APIRouter
from backend.app.schemas.rag import RetrievalQuery, RetrievalResult
from backend.app.services.literature_service import LiteratureService

router = APIRouter(prefix="/literature", tags=["Literature"])
lit_service = LiteratureService()


@router.post("/search", response_model=RetrievalResult)
def search_literature(query: RetrievalQuery):
    return lit_service.search(query)
