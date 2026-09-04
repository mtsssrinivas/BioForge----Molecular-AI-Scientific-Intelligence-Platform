"""
Unit tests for Scientific Literature Retrieval and Vector Store (Phase 5)
"""

import pytest
from pathlib import Path
from backend.app.schemas.rag import DocumentInput, RetrievalQuery
from backend.app.rag.chunker import ScientificChunker
from backend.app.rag.embeddings import LocalScientificEmbeddingProvider
from backend.app.rag.vector_store import VectorStore
from backend.app.services.literature_service import LiteratureService


def test_chunker_and_citation_preservation():
    chunker = ScientificChunker(target_chunk_size=200)
    doc = DocumentInput(
        title="ESOL: Estimating Aqueous Solubility Directly from Molecular Structure",
        authors="John S. Delaney",
        source="JCICS",
        publication_year=2004,
        abstract="A model for estimating aqueous solubility from molecular structure.",
        full_text="Methods: The regression relies on cLogP and Molecular Weight.",
    )

    chunks = chunker.chunk_document("DOC-001", doc)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.document_id == "DOC-001"
        assert chunk.title == doc.title
        assert chunk.citation_reference.startswith("[Delaney2004")
        assert len(chunk.content) > 0


def test_embedding_provider_consistency():
    provider = LocalScientificEmbeddingProvider(dimension=384, seed=42)
    vec1 = provider.embed_text("Aqueous solubility LogP molecular weight")
    vec2 = provider.embed_text("Aqueous solubility LogP molecular weight")

    assert len(vec1) == 384
    assert vec1 == vec2  # Perfectly deterministic


def test_vector_retrieval_and_filtering():
    service = LiteratureService()
    fixture_path = Path("data/raw/scientific_literature.json")
    assert fixture_path.exists()

    count = service.ingest_fixture_file(fixture_path)
    assert count == 4

    # Search for solubility
    query = RetrievalQuery(query="aqueous solubility Delaney LogP molecular weight", top_k=2)
    result = service.search(query)

    assert result.total_found > 0
    top_chunk = result.evidence[0]
    assert "Delaney" in top_chunk.authors or "Solubility" in top_chunk.title
    assert top_chunk.relevance_score is not None
    assert top_chunk.relevance_score > 0.0
    assert top_chunk.citation_reference.startswith("[")


def test_metadata_filtering():
    service = LiteratureService()
    # Filter by source
    query = RetrievalQuery(
        query="graph neural network",
        top_k=5,
        source_filter="NeurIPS",
    )
    result = service.search(query)

    for chunk in result.evidence:
        assert "NeurIPS" in chunk.source
