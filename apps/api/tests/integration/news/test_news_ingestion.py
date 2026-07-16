from sqlalchemy.orm import Session

from app.integrations.news.base import RawNewsItem
from app.integrations.news.config import NewsSourceConfig
from app.models.company import Company
from app.models.news_article import NewsArticle
from app.services.news_ingestion_service import NewsIngestionService


def test_ingestion_is_idempotent_and_material_update_resets_lifecycle(
    db_session: Session,
) -> None:
    company = Company(
        name="Asteria HealthCloud",
        domain="asteria.example",
        sector="Software",
        country="France",
        extra_data={"aliases": ["Asteria"]},
    )
    db_session.add(company)
    db_session.flush()
    source = NewsSourceConfig(
        source_id="demo",
        adapter="mock",
        fixture_path="items.json",
        company_domain="asteria.example",
        reliability=0.9,
    )
    service = NewsIngestionService(db_session)
    item = RawNewsItem(
        source_item_id="one",
        title="Asteria expands",
        summary="Asteria opened an office.",
        url="https://news.example/article?utm_source=x",
        published_at="2026-07-10T09:00:00Z",
    )

    created = service.ingest(item, source)
    duplicate = service.ingest(item, source)
    row = db_session.query(NewsArticle).one()
    row.trigger_extraction_status = "processed"
    row.trigger_extraction_version = "m3-rules-v1"
    updated = service.ingest(
        RawNewsItem(
            source_item_id="one",
            title="Asteria expands",
            summary="Asteria opened two offices.",
            url="https://news.example/article",
            published_at="2026-07-10T09:00:00Z",
        ),
        source,
    )

    assert created.action == "created"
    assert duplicate.action == "duplicate"
    assert updated.action == "updated"
    assert db_session.query(NewsArticle).count() == 1
    assert row.company_id == company.id
    assert row.external_id == "demo:one"
    assert row.trigger_extraction_status == "pending"
    assert row.trigger_extraction_version is None
