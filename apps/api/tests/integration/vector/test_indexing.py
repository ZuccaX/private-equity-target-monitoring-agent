from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_indexing_service import DocumentIndexingService
from app.services.embedding_service import EmbeddingService
from app.services.embeddings.base import EmbeddingIdentity
from app.services.embeddings.hashing import HashingEmbeddingProvider


class FakeSemanticProvider:
    identity = EmbeddingIdentity(
        "sentence_transformer",
        "sentence-transformers/all-MiniLM-L6-v2",
        "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        384,
    )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0, 1.0] + [0.0] * 382 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def _document(db: Session) -> Document:
    company = Company(
        name="Index Co",
        domain="index.example",
        sector="Software",
        country="France",
    )
    db.add(company)
    db.flush()
    document = Document(
        company_id=company.id,
        title="Investment memo",
        file_name="memo.txt",
        document_type="memo",
        source_system="fixture",
        content_text="healthcare recurring revenue growth",
        external_id="index-doc",
    )
    db.add(document)
    db.commit()
    return document


def test_indexing_preserves_current_cohorts_and_invalidates_stale_content(
    db_session: Session,
) -> None:
    document = _document(db_session)
    hashing = EmbeddingService(HashingEmbeddingProvider())
    semantic = EmbeddingService(FakeSemanticProvider())

    first = DocumentIndexingService(
        db_session, embedding_services=[hashing, semantic]
    ).index_all_documents()

    assert first.chunks_created == 2
    assert db_session.query(DocumentChunk).count() == 2

    document.content_text = "industrial automation expansion"
    db_session.commit()
    second = DocumentIndexingService(
        db_session, embedding_services=[hashing]
    ).index_all_documents()

    rows = db_session.query(DocumentChunk).all()
    assert second.chunks_created == 1
    assert len(rows) == 1
    assert rows[0].chunk_text == "industrial automation expansion"
    assert rows[0].embedding_provider == "hashing"


def test_same_cohort_reindex_replaces_instead_of_duplicates(
    db_session: Session,
) -> None:
    _document(db_session)
    service = DocumentIndexingService(db_session)
    service.index_all_documents()
    service.index_all_documents()

    assert db_session.query(DocumentChunk).count() == 1
