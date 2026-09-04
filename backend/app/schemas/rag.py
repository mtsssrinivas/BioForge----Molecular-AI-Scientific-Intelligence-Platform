"""
Schemas for Scientific Literature Retrieval and RAG System
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    title: str
    authors: str
    source: str = "PubMed"
    publication_year: int = 2023
    doi: Optional[str] = None
    abstract: str
    full_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LiteratureChunkSchema(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    title: str
    authors: str
    source: str
    publication_year: int
    content: str
    citation_reference: str
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalQuery(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=20)
    min_similarity: float = Field(default=0.1, ge=0.0, le=1.0)
    source_filter: Optional[str] = None
    year_min: Optional[int] = None


class RetrievalResult(BaseModel):
    query: str
    total_found: int
    evidence: List[LiteratureChunkSchema]


class ScientificRAGRequest(BaseModel):
    question: str
    smiles: Optional[str] = None
    model_prediction: Optional[float] = None
    top_k: int = 3


class ScientificRAGResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    evidence: List[LiteratureChunkSchema]
    citations: List[str]
    limitations: str
    molecular_context: Optional[Dict[str, Any]] = None
