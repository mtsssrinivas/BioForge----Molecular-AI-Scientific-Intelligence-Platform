"""
Scientific Document Chunking Module
Splits scientific text into context-preserving chunks with citation keys and section metadata.
"""

from typing import List, Dict, Any
import re
import uuid
from backend.app.schemas.rag import DocumentInput, LiteratureChunkSchema


class ScientificChunker:
    """Chunks scientific articles into semantic segments while maintaining document provenance."""

    def __init__(self, target_chunk_size: int = 400, chunk_overlap: int = 50):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def generate_citation_key(self, doc: DocumentInput, chunk_idx: int) -> str:
        first_author_str = doc.authors.split(",")[0].strip()
        name_parts = [p.strip() for p in first_author_str.split(" ") if p.strip()]
        last_name = name_parts[-1] if name_parts else "Ref"
        # Sanitize author string
        author_clean = re.sub(r"[^A-Za-z0-9]", "", last_name)
        return f"[{author_clean}{doc.publication_year}_c{chunk_idx + 1}]"

    def chunk_document(self, doc_id: str, doc: DocumentInput) -> List[LiteratureChunkSchema]:
        text = f"{doc.title}.\n\nAbstract: {doc.abstract}"
        if doc.full_text:
            text += f"\n\n{doc.full_text}"

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) > self.target_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(current_chunk.strip())

        # If still only 1 or 0 chunks, split by sentences
        if len(chunks) == 0:
            chunks = [text]

        results = []
        for idx, content in enumerate(chunks):
            citation_key = self.generate_citation_key(doc, idx)
            chunk_schema = LiteratureChunkSchema(
                id=f"CHK-{uuid.uuid4().hex[:10].upper()}",
                document_id=doc_id,
                chunk_index=idx,
                title=doc.title,
                authors=doc.authors,
                source=doc.source,
                publication_year=doc.publication_year,
                content=content,
                citation_reference=citation_key,
                metadata={
                    "doi": doc.doi,
                    "section": "Abstract" if idx == 0 else "Content",
                    **doc.metadata,
                },
            )
            results.append(chunk_schema)

        return results
