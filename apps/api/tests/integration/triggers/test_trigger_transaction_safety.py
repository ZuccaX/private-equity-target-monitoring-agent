from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.news_article import NewsArticle
from app.models.trigger import Trigger
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.trigger_batch_service import TriggerBatchService


class FailingAuditRepository(AuditLogRepository):
    def create(self, audit_log: AuditLog) -> AuditLog:
        raise RuntimeError("simulated audit failure")


def test_audit_failure_rolls_back_article_and_trigger(db_session: Session) -> None:
    company = Company(
        name="Asteria",
        domain="asteria.example",
        sector="Software",
        country="France",
        extra_data={},
    )
    db_session.add(company)
    db_session.flush()
    article = NewsArticle(
        company_id=company.id,
        title="Asteria launched a new platform.",
        source="fixture",
        raw_payload={},
        content_hash="a" * 64,
        external_id="fixture:audit",
    )
    db_session.add(article)
    db_session.commit()
    article_id = article.id

    report = TriggerBatchService(
        db_session,
        audit_repository=FailingAuditRepository(db_session),
    ).process(article_ids=[article_id])

    db_session.expire_all()
    assert report.status == "failed"
    assert db_session.query(Trigger).count() == 0
    assert (
        db_session.get(NewsArticle, article_id).trigger_extraction_status
        == "pending"
    )
    assert db_session.query(AuditLog).count() == 0
