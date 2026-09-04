"""
Scientific RAG reasoning endpoints
"""

from fastapi import APIRouter
from backend.app.schemas.rag import ScientificRAGRequest, ScientificRAGResponse
from backend.app.rag.engine import ScientificRAGEngine

router = APIRouter(prefix="/rag", tags=["Scientific RAG"])
_rag_engine = None


def get_rag_engine() -> ScientificRAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = ScientificRAGEngine()
    return _rag_engine


@router.post("/query", response_model=ScientificRAGResponse)
def query_scientific_rag(req: ScientificRAGRequest):
    return get_rag_engine().answer_question(req)
