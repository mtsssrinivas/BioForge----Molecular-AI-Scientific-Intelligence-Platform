"""
Vector Storage and Semantic Retrieval Engine
Provides cosine similarity vector search with metadata filtering.
Compatible with PostgreSQL pgvector and relational vector storage.
"""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from backend.app.schemas.rag import LiteratureChunkSchema, RetrievalQuery
from backend.app.rag.embeddings import get_embedding_provider, BaseEmbeddingProvider
from backend.app.core.logging import logger


class VectorStore:
    """In-memory and relational vector index supporting cosine similarity search and metadata filtering."""

    def __init__(self, embedding_provider: Optional[BaseEmbeddingProvider] = None):
        self.provider = embedding_provider or get_embedding_provider()
        self.chunks: List[LiteratureChunkSchema] = []
        self.vectors: Optional[np.ndarray] = None  # Shape [N, D]

    def add_chunks(self, chunks: List[LiteratureChunkSchema]):
        if not chunks:
            return

        texts = [c.content for c in chunks]
        new_vecs = np.array(self.provider.embed_batch(texts), dtype=np.float32)

        # Append chunks and vectors
        self.chunks.extend(chunks)
        if self.vectors is None:
            self.vectors = new_vecs
        else:
            self.vectors = np.vstack([self.vectors, new_vecs])

        logger.info(f"VectorStore: Indexed {len(chunks)} new chunks (Total: {len(self.chunks)})")

    def search(self, query: RetrievalQuery) -> List[LiteratureChunkSchema]:
        if not self.chunks or self.vectors is None or len(self.vectors) == 0:
            return []

        # 1. Embed query
        q_vec = np.array(self.provider.embed_text(query.query), dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm < 1e-8:
            return []
        q_vec = q_vec / q_norm

        # 2. Compute cosine similarity against all indexed vectors
        scores = np.dot(self.vectors, q_vec)

        # 3. Apply metadata filters and collect candidate matches
        scored_candidates: List[Tuple[float, LiteratureChunkSchema]] = []
        for idx, score in enumerate(scores):
            if score < query.min_similarity:
                continue

            chunk = self.chunks[idx]

            # Source filter
            if query.source_filter and query.source_filter.lower() not in chunk.source.lower():
                continue

            # Year filter
            if query.year_min and chunk.publication_year < query.year_min:
                continue

            # Create copy with populated relevance score
            chunk_copy = chunk.model_copy(update={"relevance_score": round(float(score), 4)})
            scored_candidates.append((float(score), chunk_copy))

        # 4. Sort descending by similarity score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # 5. Return top-k
        return [c for _, c in scored_candidates[: query.top_k]]
