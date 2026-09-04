"""
Scientific literature endpoints
"""

from fastapi import APIRouter
from backend.app.schemas.rag import RetrievalQuery, RetrievalResult
from backend.app.services.literature_service import LiteratureService

router = APIRouter(prefix="/literature", tags=["Literature"])
_lit_service = None


def get_lit_service() -> LiteratureService:
    global _lit_service
    if _lit_service is None:
        _lit_service = LiteratureService()
    return _lit_service


@router.post("/search", response_model=RetrievalResult)
def search_literature(query: RetrievalQuery):
    return get_lit_service().search(query)
