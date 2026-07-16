from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.news_article import NewsArticle
from app.models.trigger import Trigger
from app.services.trigger_batch_service import TriggerBatchService


def _article(db: Session, company_id: int, title: str, summary: str) -> NewsArticle:
    article = NewsArticle(
        company_id=company_id,
        title=title,
        summary=summary,
        source="fixture",
        raw_payload={},
        content_hash=f"{title:0<64}"[:64],
        external_id=f"fixture:{title}",
    )
    db.add(article)
    db.flush()
    return article


def test_batch_tracks_processed_no_trigger_and_idempotency(
    db_session: Session,
) -> None:
    company = Company(
        name="Asteria",
        domain="asteria.example",
        sector="Software",
        country="France",
        extra_data={},
    )
    db_session.add(company)
    db_session.flush()
    positive = _article(
        db_session,
        company.id,
        "Asteria launched a new platform.",
        "The launch occurred on 2026-07-10.",
    )
    empty = _article(
        db_session,
        company.id,
        "Routine policy update",
        "The handbook was refreshed.",
    )
    db_session.commit()

    first = TriggerBatchService(db_session).process(
        article_ids=[positive.id, empty.id]
    )
    second = TriggerBatchService(db_session).process(
        article_ids=[positive.id, empty.id]
    )

    assert first.status == "ok"
    assert first.succeeded == 2
    assert first.triggers_created == 1
    assert db_session.get(NewsArticle, positive.id).trigger_extraction_status == "processed"
    assert db_session.get(NewsArticle, empty.id).trigger_extraction_status == "no_trigger"
    assert db_session.query(Trigger).count() == 1
    assert second.selected == 0


def test_negative_trigger_persists_as_negative(db_session: Session) -> None:
    company = Company(
        name="Esker",
        domain="esker.example",
        sector="Software",
        country="France",
        extra_data={},
    )
    db_session.add(company)
    db_session.flush()
    article = _article(
        db_session,
        company.id,
        "Esker lost its largest customer.",
        "The contract will not renew.",
    )
    db_session.commit()

    TriggerBatchService(db_session).process(article_ids=[article.id])

    assert db_session.query(Trigger).one().is_negative is True
