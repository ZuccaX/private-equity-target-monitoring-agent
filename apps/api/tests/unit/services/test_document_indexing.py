from types import SimpleNamespace
from unittest.mock import MagicMock, Mock
import pytest

from app.services.document_indexing_service import DocumentIndexingService
from app.services.embeddings.base import EmbeddingIdentity


class FakeEmbeddingService:
    def __init__(self, provider: str, *, fail: bool = False) -> None:
        self.identity = EmbeddingIdentity(provider, provider, "v1", 384)
        self.fail = fail
        self.calls: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.fail:
            raise RuntimeError("provider failed")
        return [[1.0] + [0.0] * 383 for _ in texts]


def test_indexing_batches_chunks_and_keeps_successful_provider() -> None:
    db = MagicMock()
    hashing = FakeEmbeddingService("hashing")
    semantic = FakeEmbeddingService("sentence_transformer", fail=True)
    service = DocumentIndexingService(
        db,
        embedding_services=[hashing, semantic],
    )
    service.document_chunk_repository.delete_stale_sources = Mock(return_value=0)
    service.document_chunk_repository.delete_exact_cohort = Mock(return_value=0)
    service.document_repository.list_all = Mock(
        return_value=[
            SimpleNamespace(
                id=1,
                company_id=1,
                title="Memo",
                document_type="memo",
                source_system="fixture",
                content_text="one two three",
                content_hash=None,
                file_version=None,
                indexed_at=None,
            )
        ]
    )

    summary = service.index_all_documents()

    assert hashing.calls == [["one two three"]]
    assert semantic.calls == [["one two three"]]
    assert summary.documents_indexed == 1
    assert summary.chunks_created == 1
    assert summary.provider_failures == ("sentence_transformer:RuntimeError",)
    db.commit.assert_called_once()


def test_wrong_dimension_creates_no_chunks() -> None:
    provider = FakeEmbeddingService("broken")
    provider.embed_documents = Mock(return_value=[[0.0] * 383])
    db = Mock()
    service = DocumentIndexingService(db, embedding_services=[provider])
    service.document_chunk_repository.delete_stale_sources = Mock(return_value=0)
    service.document_repository.list_all = Mock(
        return_value=[
            SimpleNamespace(
                id=1,
                company_id=1,
                title="Memo",
                document_type="memo",
                source_system="fixture",
                content_text="content",
                content_hash=None,
                file_version=None,
                indexed_at=None,
            )
        ]
    )

    with pytest.raises(RuntimeError, match="All embedding providers failed"):
        service.index_all_documents()

    db.add.assert_not_called()
    db.rollback.assert_called_once()
