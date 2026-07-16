from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

API_DIRECTORY = Path(__file__).resolve().parents[1]
if str(API_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(API_DIRECTORY))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import assert_safe_test_database_url, settings
from app.models.company import Company
from app.models.document import Document
from app.schemas.vector_search import RAGRetrievalRequest
from app.services.rag_retrieval_service import RAGRetrievalService
from app.services.retrieval_evaluation_service import (
    EvaluationObservation,
    RetrievalEvaluationService,
    RetrievalMetrics,
)


def evaluate_session(db: Session, fixture_path: Path) -> RetrievalMetrics:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    observations: list[EvaluationObservation] = []
    for case in fixture:
        company = db.query(Company).filter_by(domain=case["company_domain"]).one()
        response = RAGRetrievalService(db).retrieve(
            RAGRetrievalRequest(
                query=case["query"],
                company_id=company.id,
                top_k=case["top_k"],
                document_types=case["allowed_types"],
                minimum_similarity=case["minimum_similarity"],
            )
        )
        observations.append(
            EvaluationObservation(
                case_id=case["case_id"],
                expected_documents=frozenset(case["expected_documents"]),
                forbidden_documents=frozenset(case["forbidden_documents"]),
                ranked_documents=tuple(
                    db.get(Document, source.document_id).external_id
                    for source in response.sources
                ),
                empty=response.status == "empty",
                fallback_used=response.fallback_used,
                warnings=tuple(response.warnings),
            )
        )
    return RetrievalEvaluationService().calculate(observations)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument(
        "--fixture", type=Path, default=settings.retrieval_evaluation_fixture
    )
    args = parser.parse_args()
    assert_safe_test_database_url(args.database_url)
    engine = create_engine(args.database_url)
    with sessionmaker(bind=engine)() as db:
        print(evaluate_session(db, args.fixture))
    engine.dispose()


if __name__ == "__main__":
    main()
