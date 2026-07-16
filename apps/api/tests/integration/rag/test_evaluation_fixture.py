import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.company import Company
from app.models.document import Document
from app.schemas.vector_search import RAGRetrievalRequest
from app.services.demo_seed_service import DemoSeedService
from app.services.document_indexing_service import DocumentIndexingService
from app.services.rag_retrieval_service import RAGRetrievalService
from app.services.retrieval_evaluation_service import (
    EvaluationObservation,
    RetrievalEvaluationService,
)


def test_deterministic_evaluation_fixture_has_full_recall_and_zero_leakage(
    db_session: Session,
) -> None:
    DemoSeedService(db_session, settings.seed_data_dir).seed()
    DocumentIndexingService(db_session).index_all_documents()
    fixture = json.loads(
        settings.retrieval_evaluation_fixture.read_text(encoding="utf-8")
    )
    observations: list[EvaluationObservation] = []
    for case in fixture:
        company = db_session.query(Company).filter_by(
            domain=case["company_domain"]
        ).one()
        response = RAGRetrievalService(db_session).retrieve(
            RAGRetrievalRequest(
                query=case["query"],
                company_id=company.id,
                top_k=case["top_k"],
                document_types=case["allowed_types"],
                minimum_similarity=case["minimum_similarity"],
            )
        )
        ranked = tuple(
            db_session.get(Document, source.document_id).external_id
            for source in response.sources
        )
        observations.append(
            EvaluationObservation(
                case_id=case["case_id"],
                expected_documents=frozenset(case["expected_documents"]),
                forbidden_documents=frozenset(case["forbidden_documents"]),
                ranked_documents=ranked,
                empty=response.status == "empty",
                fallback_used=response.fallback_used,
                warnings=tuple(response.warnings),
            )
        )
        assert (response.status == "empty") is case["expect_empty"]
        if case["expect_warning"]:
            assert case["expect_warning"] in response.warnings

    metrics = RetrievalEvaluationService().calculate(observations)
    assert metrics.recall_at_k == 1.0
    assert metrics.leakage_count == 0
    assert metrics.empty_count == 1
