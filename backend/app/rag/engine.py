"""
Scientific RAG Engine
End-to-end evidence retrieval, context assembly, and scientific question answering.
"""

from typing import Optional, Dict, Any
from backend.app.schemas.rag import (
    ScientificRAGRequest,
    ScientificRAGResponse,
    RetrievalQuery,
)
from backend.app.services.literature_service import LiteratureService, vector_store
from backend.app.rag.llm import ScientificEvidenceSynthesizer
from backend.app.ml.evaluate_xgb import predict_smiles


class ScientificRAGEngine:
    def __init__(self, literature_service: Optional[LiteratureService] = None):
        self.lit_service = literature_service or LiteratureService()
        self.synthesizer = ScientificEvidenceSynthesizer()

    def answer_question(self, req: ScientificRAGRequest) -> ScientificRAGResponse:
        # 1. Retrieve evidence
        retrieval_query = RetrievalQuery(
            query=req.question,
            top_k=req.top_k,
            min_similarity=0.10,
        )
        search_result = self.lit_service.search(retrieval_query)
        evidence_chunks = search_result.evidence

        # 2. Molecular context if requested
        mol_ctx: Optional[Dict[str, Any]] = None
        if req.smiles:
            try:
                pred_res = predict_smiles(req.smiles)
                mol_ctx = {
                    "smiles": req.smiles,
                    "canonical_smiles": pred_res.canonical_smiles,
                    "predicted_value": pred_res.predicted_value,
                    "unit": pred_res.unit,
                    "model_id": pred_res.model_id,
                    "descriptors": pred_res.descriptors,
                }
            except Exception:
                mol_ctx = {"smiles": req.smiles, "status": "Failed to compute molecular prediction"}

        # 3. Grounded answer synthesis
        synthesis = self.synthesizer.synthesize_answer(
            question=req.question,
            evidence=evidence_chunks,
            molecular_context=mol_ctx,
        )

        return ScientificRAGResponse(
            question=req.question,
            answer=synthesis["answer"],
            confidence=synthesis["confidence"],
            evidence=evidence_chunks,
            citations=synthesis["citations"],
            limitations=synthesis["limitations"],
            molecular_context=mol_ctx,
        )
