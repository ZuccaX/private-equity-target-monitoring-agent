from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.integrations.news.config import NewsSourceRegistry
from app.schemas.news_article import NewsArticleRead, NewsSyncRequest
from app.services.news_sync_service import NewsSyncOrchestrator, NewsSyncReport
from app.services.news_article_service import NewsArticleService


router = APIRouter(
    prefix="/api/news-articles",
    tags=["news-articles"],
)


@router.get("", response_model=list[NewsArticleRead])
def list_news_articles(
    company_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[NewsArticleRead]:
    service = NewsArticleService(db)

    return service.list_news_articles(company_id=company_id)


@router.post("/sync", response_model=NewsSyncReport)
def sync_news_articles(
    request: NewsSyncRequest,
    db: Session = Depends(get_db),
) -> NewsSyncReport:
    if not settings.news_sync_api_effective:
        raise HTTPException(status_code=403, detail="News sync action is disabled.")
    registry = NewsSourceRegistry.load(
        settings.news_source_config,
        fixture_root=settings.news_fixture_root,
    )
    try:
        report = NewsSyncOrchestrator(
            db, registry=registry, settings=settings
        ).sync(
            source_ids=request.source_ids,
            extract_triggers=request.extract_triggers,
            max_items_per_source=request.max_items_per_source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if report.status == "failed":
        raise HTTPException(status_code=503, detail="All news sources failed.")
    return report
