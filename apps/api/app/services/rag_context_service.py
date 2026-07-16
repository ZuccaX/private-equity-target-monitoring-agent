from __future__ import annotations

from dataclasses import dataclass

from app.schemas.vector_search import RAGCitation, VectorSearchResultRead
from app.services.rag_safety_service import RAGSafetyService


@dataclass(frozen=True)
class RAGContext:
    context: str
    sources: list[VectorSearchResultRead]
    citations: list[RAGCitation]
    warnings: list[str]


class RAGContextService:
    def __init__(self, safety: RAGSafetyService | None = None) -> None:
        self.safety = safety or RAGSafetyService()

    def build(
        self,
        results: list[VectorSearchResultRead],
        *,
        max_words: int,
    ) -> RAGContext:
        seen_documents: set[int] = set()
        selected: list[VectorSearchResultRead] = []
        citations: list[RAGCitation] = []
        warnings: list[str] = []
        blocks: list[str] = []
        remaining = max_words
        for result in results:
            if result.document_id in seen_documents or remaining <= 0:
                continue
            safe_text, safety_warnings = self.safety.isolate_untrusted_text(
                result.chunk_text
            )
            words = safe_text.split()
            if len(words) > remaining:
                words = words[:remaining]
                warnings.append("context_word_budget_truncated")
            if not words:
                continue
            source_number = len(selected) + 1
            blocks.append(
                f"[Source {source_number}] Document: {result.document_title}\n"
                f"Document ID: {result.document_id}\n"
                f"Document Type: {result.document_type}\n"
                f"Source System: {result.source_system}\n"
                f"Source Path: {result.source_path or 'N/A'}\n"
                f"Chunk Index: {result.chunk_index}\n"
                f"Similarity: {result.similarity:.4f}\n\n"
                + " ".join(words)
            )
            selected.append(result)
            citations.append(
                RAGCitation(
                    source_number=source_number,
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    document_title=result.document_title,
                    source_path=result.source_path,
                )
            )
            seen_documents.add(result.document_id)
            remaining -= len(words)
            warnings.extend(safety_warnings)
        return RAGContext(
            context="\n\n---\n\n".join(blocks),
            sources=selected,
            citations=citations,
            warnings=list(dict.fromkeys(warnings)),
        )
