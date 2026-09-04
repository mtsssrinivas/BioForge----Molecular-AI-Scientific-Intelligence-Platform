"""
Literature Service
Orchestrates document ingestion, chunking, relational persistence, and vector indexing.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import uuid
from sqlalchemy.orm import Session

from backend.app.schemas.rag import (
    DocumentInput,
    LiteratureChunkSchema,
    RetrievalQuery,
    RetrievalResult,
)
from backend.app.rag.chunker import ScientificChunker
from backend.app.rag.vector_store import VectorStore
from backend.app.db.models import LiteratureDocument, LiteratureChunk
from backend.app.core.logging import logger

# Singleton vector store instance for runtime semantic retrieval
vector_store = VectorStore()


class LiteratureService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.chunker = ScientificChunker()
        self.vector_store = vector_store

    def ingest_document(self, doc_input: DocumentInput) -> str:
        doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"

        chunks = self.chunker.chunk_document(doc_id, doc_input)
        self.vector_store.add_chunks(chunks)

        if self.db:
            db_doc = LiteratureDocument(
                id=doc_id,
                title=doc_input.title,
                authors=doc_input.authors,
                source=doc_input.source,
                publication_year=doc_input.publication_year,
                doi=doc_input.doi,
                abstract=doc_input.abstract,
                metadata_json=doc_input.metadata,
            )
            self.db.add(db_doc)

            for chunk in chunks:
                db_chunk = LiteratureChunk(
                    id=chunk.id,
                    document_id=doc_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    citation_reference=chunk.citation_reference,
                    metadata_json=chunk.metadata,
                )
                self.db.add(db_chunk)

            self.db.commit()

        logger.info(f"Ingested document: '{doc_input.title}' ({len(chunks)} chunks)")
        return doc_id

    def ingest_fixture_file(self, json_path: Path) -> int:
        if not json_path.exists():
            raise FileNotFoundError(f"Fixture file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            docs_data = json.load(f)

        count = 0
        for item in docs_data:
            doc_in = DocumentInput(**item)
            self.ingest_document(doc_in)
            count += 1
        return count

    def search(self, query: RetrievalQuery) -> RetrievalResult:
        results = self.vector_store.search(query)
        return RetrievalResult(
            query=query.query,
            total_found=len(results),
            evidence=results,
        )
