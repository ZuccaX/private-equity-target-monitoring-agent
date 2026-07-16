from app.schemas.vector_search import VectorSearchResultRead
from app.services.rag_context_service import RAGContextService


def _result(chunk_id: int, document_id: int, text: str) -> VectorSearchResultRead:
    return VectorSearchResultRead(
        chunk_id=chunk_id,
        document_id=document_id,
        company_id=1,
        document_title=f"Document {document_id}",
        document_type="memo",
        source_system="fixture",
        source_path=None,
        chunk_index=0,
        chunk_text=text,
        token_count=len(text.split()),
        embedding_model="local-hashing-384-v1",
        embedding_provider="hashing",
        embedding_model_version="1",
        embedding_dimension=384,
        distance=0.1,
        similarity=0.9,
    )


def test_context_enforces_diversity_budget_and_citations() -> None:
    built = RAGContextService().build(
        [
            _result(1, 10, "one two three"),
            _result(2, 10, "duplicate document"),
            _result(3, 20, "four five six"),
        ],
        max_words=5,
    )

    assert [source.chunk_id for source in built.sources] == [1, 3]
    assert len(built.citations) == 2
    assert "six" not in built.context
    assert "context_word_budget_truncated" in built.warnings
