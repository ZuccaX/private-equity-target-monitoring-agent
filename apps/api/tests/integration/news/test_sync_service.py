from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.news.config import NewsSourceRegistry
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.news_article import NewsArticle
from app.models.trigger import Trigger
from app.services.news_sync_service import NewsSyncOrchestrator


def _seed_companies(db: Session) -> None:
    for name, domain in (
        ("Asteria HealthCloud", "asteria.example"),
        ("Esker Logistics", "esker.example"),
        ("Fjord Specialty Services", "fjord.example"),
    ):
        db.add(
            Company(
                name=name,
                domain=domain,
                sector="Software",
                country="France",
                extra_data={},
            )
        )
    db.commit()


def test_mock_sync_is_offline_idempotent_and_extracts_negative_triggers(
    db_session: Session,
) -> None:
    _seed_companies(db_session)
    settings = Settings(_env_file=None)
    registry = NewsSourceRegistry.load(
        settings.news_source_config,
        fixture_root=settings.news_fixture_root,
    )
    orchestrator = NewsSyncOrchestrator(
        db_session, registry=registry, settings=settings
    )

    first = orchestrator.sync(source_ids=["demo_mock"], extract_triggers=True)
    second = orchestrator.sync(source_ids=["demo_mock"], extract_triggers=True)

    assert first.status == "ok"
    assert first.created == 3
    assert first.triggers_created == 2
    assert second.duplicates == 3
    assert db_session.query(NewsArticle).count() == 3
    assert db_session.query(Trigger).count() == 2
    assert db_session.query(Trigger).filter_by(is_negative=True).count() == 1
    assert db_session.query(AuditLog).filter_by(action="news_sync").count() == 2


def test_unknown_source_is_validation_error(db_session: Session) -> None:
    settings = Settings(_env_file=None)
    registry = NewsSourceRegistry.load(
        settings.news_source_config,
        fixture_root=settings.news_fixture_root,
    )
    orchestrator = NewsSyncOrchestrator(
        db_session, registry=registry, settings=settings
    )

    try:
        orchestrator.sync(source_ids=["unknown"])
    except ValueError as exc:
        assert "not enabled" in str(exc)
    else:
        raise AssertionError("unknown source must fail validation")
