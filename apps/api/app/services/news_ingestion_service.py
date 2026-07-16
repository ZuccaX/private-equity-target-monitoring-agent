from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.integrations.news.base import RawNewsItem
from app.integrations.news.config import NewsSourceConfig
from app.integrations.news.normalization import (
    content_hash,
    detect_language,
    normalize_text,
    normalize_url,
    parse_datetime_utc,
    sanitize_html,
)
from app.models.news_article import NewsArticle
from app.repositories.company_repository import CompanyRepository
from app.repositories.news_article_repository import NewsArticleRepository
from app.services.news_company_matcher import NewsCompanyMatcher


class NewsIngestionError(ValueError):
    def __init__(self, category: str) -> None:
        super().__init__(category)
        self.category = category


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    article: NewsArticle
    action: str


class NewsIngestionService:
    def __init__(
        self,
        db: Session,
        *,
        matcher: NewsCompanyMatcher | None = None,
    ) -> None:
        self.db = db
        self.company_repository = CompanyRepository(db)
        self.news_repository = NewsArticleRepository(db)
        self.matcher = matcher or NewsCompanyMatcher()

    def ingest(
        self,
        item: RawNewsItem,
        source: NewsSourceConfig,
    ) -> IngestionOutcome:
        match = self.matcher.match(
            item, source, self.company_repository.list_matchable()
        )
        if not match.accepted or match.company_id is None:
            raise NewsIngestionError(match.category or "company_not_found")

        title = normalize_text(item.title, max_length=500)
        if not title:
            raise NewsIngestionError("missing_title")
        summary_source = item.content or item.summary
        summary = sanitize_html(summary_source, max_length=5_000) or None
        try:
            canonical_url = normalize_url(
                item.url,
                allowed_query_keys=set(source.allowed_query_keys),
            )
            published_at = parse_datetime_utc(item.published_at)
        except ValueError as exc:
            raise NewsIngestionError("invalid_item") from exc
        identity_hash = content_hash(title, summary)
        external_id = (
            f"{source.source_id}:{item.source_item_id}"
            if item.source_item_id
            else None
        )
        existing = self.news_repository.find_identity(
            external_id=external_id,
            company_id=match.company_id,
            canonical_url=canonical_url,
            content_hash=identity_hash,
        )
        if existing is not None and existing.company_id != match.company_id:
            raise NewsIngestionError("company_identity_conflict")
        if existing is not None and existing.content_hash == identity_hash:
            return IngestionOutcome(existing, "duplicate")

        article = existing or NewsArticle(company_id=match.company_id)
        action = "updated" if existing is not None else "created"
        article.company_id = match.company_id
        article.title = title
        article.summary = summary
        article.url = canonical_url
        article.canonical_url = canonical_url
        article.source = source.source_id
        article.published_at = published_at
        article.content_hash = identity_hash
        article.language = (
            item.language
            or source.language
            or detect_language(f"{title} {summary or ''}")
        )
        article.source_reliability = source.reliability
        article.company_match_confidence = match.confidence
        article.ingestion_status = "updated" if existing else "ingested"
        article.external_id = external_id or article.external_id
        article.raw_payload = {
            "source_item_id": item.source_item_id,
            "metadata_keys": sorted(item.metadata)[:20],
        }
        if action == "updated":
            article.trigger_extraction_status = "pending"
            article.trigger_extracted_at = None
            article.trigger_extraction_version = None
        if existing is None:
            self.news_repository.create(article)
        else:
            self.db.flush()
        return IngestionOutcome(article, action)
