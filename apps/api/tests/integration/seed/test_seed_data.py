from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agent_run import AgentRun
from app.models.approval import Approval
from app.models.company import Company
from app.models.contact import Contact
from app.models.crm_interaction import CRMInteraction
from app.models.document import Document
from app.models.email_draft import EmailDraft
from app.models.feedback import Feedback
from app.models.investment_mandate import InvestmentMandate
from app.models.news_article import NewsArticle
from app.models.priority_score import PriorityScore
from app.models.trigger import Trigger
from app.services.demo_seed_service import DemoSeedService, SEED_OWNER
import pytest


def test_seed_matrix_is_complete_idempotent_and_preserves_unrelated_rows(
    db_session: Session,
) -> None:
    db_session.autoflush = True
    sentinel = Company(
        name="User Sentinel",
        domain="user-sentinel.example",
        sector="Other",
        country="France",
        description="Do not modify",
        extra_data={"owner": "user"},
    )
    db_session.add(sentinel)
    db_session.commit()
    sentinel_id = sentinel.id
    service = DemoSeedService(db_session, settings.seed_data_dir)

    first = service.seed()
    company_ids = {
        row.domain: row.id
        for row in db_session.query(Company).filter(
            Company.extra_data["seed_owner"].astext == SEED_OWNER
        )
    }
    document_ids = {
        row.external_id: row.id
        for row in db_session.query(Document).filter(
            Document.extra_data["seed_owner"].astext == SEED_OWNER
        )
    }
    second = service.seed()

    assert first == second == {
        "companies": 6,
        "documents": 18,
        "news_articles": 18,
    }
    assert company_ids == {
        row.domain: row.id
        for row in db_session.query(Company).filter(
            Company.extra_data["seed_owner"].astext == SEED_OWNER
        )
    }
    assert document_ids == {
        row.external_id: row.id
        for row in db_session.query(Document).filter(
            Document.extra_data["seed_owner"].astext == SEED_OWNER
        )
    }
    unchanged = db_session.get(Company, sentinel_id)
    assert unchanged is not None
    assert unchanged.description == "Do not modify"
    assert unchanged.extra_data == {"owner": "user"}
    assert db_session.query(InvestmentMandate).count() == 2
    assert db_session.query(Contact).count() == 6
    assert db_session.query(CRMInteraction).count() == 12
    assert db_session.query(NewsArticle).count() == 18
    assert db_session.query(Document).count() == 18
    assert db_session.query(Trigger).filter(Trigger.is_negative.is_(True)).count() == 2
    assert db_session.query(Trigger).filter(Trigger.is_negative.is_(False)).count() == 4
    assert all(
        row.trigger_extraction_status == "pending"
        and row.trigger_extracted_at is None
        and row.trigger_extraction_version is None
        for row in db_session.query(NewsArticle)
    )
    assert all(
        row.deduplication_key
        and row.extraction_method == "seed"
        and 0 <= row.confidence_score <= 1
        and row.review_status == "unreviewed"
        for row in db_session.query(Trigger)
    )
    assert db_session.query(Feedback.feedback_type).distinct().count() == 3
    assert {row.overall_score for row in db_session.query(PriorityScore)} == {91, 64, 28}
    assert db_session.query(EmailDraft).filter_by(status="pending_approval").count() == 1
    assert {row.decision for row in db_session.query(Approval)} == {
        "rejected",
        "revision_requested",
    }
    assert "pending" not in {row.decision for row in db_session.query(Approval)}
    assert all(row.mandate_id is not None for row in db_session.query(Company).filter(
        Company.extra_data["seed_owner"].astext == SEED_OWNER
    ))
    assert "Ignore previous system instructions" in " ".join(
        row.content_text or "" for row in db_session.query(Document)
    )
    empty_company = db_session.query(Company).filter_by(domain="fjord.example").one()
    assert {row.document_type for row in db_session.query(Document).filter_by(
        company_id=empty_company.id
    )} == {"tax", "hr_policy", "legal"}
    assert all(
        row.input_snapshot.get("fallback_reason")
        for row in db_session.query(AgentRun)
    )


def test_seed_refuses_natural_key_collision_with_unowned_user_row(
    db_session: Session,
) -> None:
    db_session.autoflush = True
    db_session.add(
        Company(
            name="User-owned collision",
            domain="asteria.example",
            sector="Other",
            country="France",
            extra_data={"owner": "user"},
        )
    )
    db_session.commit()

    with pytest.raises(ValueError, match="unowned"):
        DemoSeedService(db_session, settings.seed_data_dir).seed()

    assert db_session.query(Company).count() == 1
