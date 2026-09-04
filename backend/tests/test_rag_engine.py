"""
Unit tests for Evidence-Grounded Scientific RAG Engine (Phase 6)
"""

import pytest
from pathlib import Path

from backend.app.schemas.rag import ScientificRAGRequest
from backend.app.rag.engine import ScientificRAGEngine
from backend.app.services.literature_service import LiteratureService


@pytest.fixture(scope="module")
def rag_engine():
    service = LiteratureService()
    fixture_path = Path("data/raw/scientific_literature.json")
    service.ingest_fixture_file(fixture_path)
    return ScientificRAGEngine(literature_service=service)


def test_scientific_rag_grounded_answer(rag_engine):
    req = ScientificRAGRequest(
        question="How does molecular weight and LogP affect aqueous solubility according to Delaney ESOL?",
        top_k=2,
    )
    res = rag_engine.answer_question(req)

    assert res.question == req.question
    assert len(res.evidence) > 0
    assert len(res.citations) > 0
    assert any("Delaney" in c for c in res.citations)
    assert res.confidence > 0.0
    assert "Delaney" in res.answer or "solubility" in res.answer.lower()
    assert res.limitations != ""


def test_scientific_rag_with_molecular_context(rag_engine):
    aspirin = "CC(=O)Oc1ccccc1C(=O)O"
    req = ScientificRAGRequest(
        question="What factors control solubility in small molecule analgesics?",
        smiles=aspirin,
        top_k=2,
    )
    res = rag_engine.answer_question(req)

    assert res.molecular_context is not None
    assert "predicted_value" in res.molecular_context
    assert "[Model Prediction Notice]" in res.answer


def test_scientific_rag_insufficient_evidence(rag_engine):
    req = ScientificRAGRequest(
        question="What is the best sourdough bread baking recipe with whole wheat flour?",
        top_k=2,
    )
    res = rag_engine.answer_question(req)

    # Must refuse to fabricate and explicitly indicate insufficient evidence
    assert "insufficient" in res.answer.lower()
    assert res.confidence < 0.20
