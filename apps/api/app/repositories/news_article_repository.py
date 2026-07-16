from sqlalchemy.orm import Session

from app.models.news_article import NewsArticle


class NewsArticleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[NewsArticle]:
        return (
            self.db.query(NewsArticle)
            .order_by(NewsArticle.published_at.desc().nullslast())
            .all()
        )

    def list_by_company_id(self, company_id: int) -> list[NewsArticle]:
        return (
            self.db.query(NewsArticle)
            .filter(NewsArticle.company_id == company_id)
            .order_by(NewsArticle.published_at.desc().nullslast())
            .all()
        )

    def get_by_id(self, news_article_id: int) -> NewsArticle | None:
        return (
            self.db.query(NewsArticle)
            .filter(NewsArticle.id == news_article_id)
            .first()
        )

    def get_by_url(self, url: str) -> NewsArticle | None:
        return (
            self.db.query(NewsArticle)
            .filter(NewsArticle.url == url)
            .first()
        )

    def get_by_external_id(self, external_id: str) -> NewsArticle | None:
        return (
            self.db.query(NewsArticle)
            .filter(NewsArticle.external_id == external_id)
            .first()
        )

    def get_by_company_canonical_url(
        self, company_id: int, canonical_url: str
    ) -> NewsArticle | None:
        return (
            self.db.query(NewsArticle)
            .filter(
                NewsArticle.company_id == company_id,
                NewsArticle.canonical_url == canonical_url,
            )
            .first()
        )

    def get_by_company_content_hash(
        self, company_id: int, identity_hash: str
    ) -> NewsArticle | None:
        return (
            self.db.query(NewsArticle)
            .filter(
                NewsArticle.company_id == company_id,
                NewsArticle.content_hash == identity_hash,
            )
            .first()
        )

    def find_identity(
        self,
        *,
        external_id: str | None,
        company_id: int,
        canonical_url: str | None,
        content_hash: str,
    ) -> NewsArticle | None:
        if external_id:
            found = self.get_by_external_id(external_id)
            if found is not None:
                return found
        if canonical_url:
            found = self.get_by_company_canonical_url(
                company_id, canonical_url
            )
            if found is not None:
                return found
        return self.get_by_company_content_hash(company_id, content_hash)

    def create(self, news_article: NewsArticle) -> NewsArticle:
        self.db.add(news_article)
        self.db.flush()

        return news_article

    def list_for_extraction(
        self,
        *,
        version: str,
        article_ids: list[int] | None = None,
        company_id: int | None = None,
        status: str = "pending",
        limit: int = 100,
    ) -> list[NewsArticle]:
        query = self.db.query(NewsArticle).filter(
            NewsArticle.trigger_extraction_status == status
        )
        query = query.filter(
            (NewsArticle.trigger_extraction_version.is_(None))
            | (NewsArticle.trigger_extraction_version != version)
        )
        if article_ids is not None:
            query = query.filter(NewsArticle.id.in_(article_ids))
        if company_id is not None:
            query = query.filter(NewsArticle.company_id == company_id)
        return query.order_by(NewsArticle.id.asc()).limit(limit).all()
