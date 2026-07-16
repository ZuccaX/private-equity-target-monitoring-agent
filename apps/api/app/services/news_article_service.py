from sqlalchemy.orm import Session

from app.repositories.news_article_repository import NewsArticleRepository
from app.schemas.news_article import NewsArticleRead


class NewsArticleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.news_article_repository = NewsArticleRepository(db)

    def list_news_articles(
        self,
        company_id: int | None = None,
    ) -> list[NewsArticleRead]:
        if company_id is None:
            news_articles = self.news_article_repository.list_all()
        else:
            news_articles = self.news_article_repository.list_by_company_id(
                company_id
            )

        return [
            NewsArticleRead.model_validate(news_article)
            for news_article in news_articles
        ]