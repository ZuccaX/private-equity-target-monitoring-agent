from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.document import Document
from app.schemas.vector_search import VectorSearchRequest
from app.services.document_indexing_service import DocumentIndexingService
from app.services.vector_search_service import VectorSearchService


def _seed_search_document(db: Session, domain: str, text: str) -> Company:
    company = Company(
        name=domain,
        domain=domain,
        sector="Software",
        country="France",
    )
    db.add(company)
    db.flush()
    db.add(
        Document(
            company_id=company.id,
            title=f"Memo {domain}",
            file_name="memo.txt",
            document_type="memo",
            source_system="fixture",
            content_text=text,
            external_id=f"doc-{domain}",
        )
    )
    db.commit()
    return company


def test_vector_search_is_company_scoped_but_global_debug_remains_available(
    db_session: Session,
) -> None:
    first = _seed_search_document(
        db_session, "first.example", "healthcare software recurring revenue"
    )
    second = _seed_search_document(
        db_session, "second.example", "healthcare clinics expansion"
    )
    DocumentIndexingService(db_session).index_all_documents()
    service = VectorSearchService(db_session)

    scoped = service.search(
        VectorSearchRequest(query="healthcare", company_id=first.id, top_k=10)
    )
    global_results = service.search(
        VectorSearchRequest(query="healthcare", top_k=10)
    )

    assert {result.company_id for result in scoped.results} == {first.id}
    assert {result.company_id for result in global_results.results} == {
        first.id,
        second.id,
    }
    assert scoped.effective_model_version == "1"


def test_vector_search_filters_type_threshold_and_unknown_identity(
    db_session: Session,
) -> None:
    company = _seed_search_document(
        db_session, "filter.example", "industrial automation growth"
    )
    DocumentIndexingService(db_session).index_all_documents()
    service = VectorSearchService(db_session)

    empty = service.search(
        VectorSearchRequest(
            query="industrial",
            company_id=company.id,
            document_types=["data_room"],
        )
    )
    assert empty.result_count == 0

    request = VectorSearchRequest(
        query="industrial",
        company_id=company.id,
        minimum_similarity=0.99,
    )
    assert service.search(request).result_count <= 1
