from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.news.config import NewsSourceRegistry
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.news_article import NewsArticle
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.news_sync_service import NewsSyncOrchestrator


class FailingAuditRepository(AuditLogRepository):
    def create(self, audit_log: AuditLog) -> AuditLog:
        raise RuntimeError("audit unavailable")


def test_source_audit_failure_rolls_back_source(db_session: Session) -> None:
    for name, domain in (
        ("Asteria", "asteria.example"),
        ("Esker", "esker.example"),
        ("Fjord", "fjord.example"),
    ):
        db_session.add(
            Company(
                name=name,
                domain=domain,
                sector="Software",
                country="France",
                extra_data={},
            )
        )
    db_session.commit()
    settings = Settings(_env_file=None)
    registry = NewsSourceRegistry.load(
        settings.news_source_config,
        fixture_root=settings.news_fixture_root,
    )

    report = NewsSyncOrchestrator(
        db_session,
        registry=registry,
        settings=settings,
        audit_repository=FailingAuditRepository(db_session),
    ).sync(source_ids=["demo_mock"], extract_triggers=False)

    assert report.status == "failed"
    assert db_session.query(NewsArticle).count() == 0
    assert db_session.query(AuditLog).count() == 0
