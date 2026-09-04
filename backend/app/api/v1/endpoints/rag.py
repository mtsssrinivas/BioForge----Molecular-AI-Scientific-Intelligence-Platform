"""
Scientific RAG reasoning endpoints
"""

from fastapi import APIRouter
from backend.app.schemas.rag import ScientificRAGRequest, ScientificRAGResponse
from backend.app.rag.engine import ScientificRAGEngine

router = APIRouter(prefix="/rag", tags=["Scientific RAG"])
rag_engine = ScientificRAGEngine()


@router.post("/query", response_model=ScientificRAGResponse)
def query_scientific_rag(req: ScientificRAGRequest):
    return rag_engine.answer_question(req)
