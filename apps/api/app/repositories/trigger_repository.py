from sqlalchemy.orm import Session

from app.models.trigger import Trigger
from datetime import datetime, timedelta


class TriggerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Trigger]:
        return (
            self.db.query(Trigger)
            .order_by(Trigger.detected_at.desc())
            .all()
        )

    def list_by_company_id(self, company_id: int) -> list[Trigger]:
        return (
            self.db.query(Trigger)
            .filter(Trigger.company_id == company_id)
            .order_by(Trigger.detected_at.desc())
            .all()
        )

    def get_by_id(self, trigger_id: int) -> Trigger | None:
        return (
            self.db.query(Trigger)
            .filter(Trigger.id == trigger_id)
            .first()
        )

    def get_by_news_article_id(
        self,
        news_article_id: int,
    ) -> Trigger | None:
        return (
            self.db.query(Trigger)
            .filter(Trigger.news_article_id == news_article_id)
            .first()
        )

    def get_by_article_type(
        self, news_article_id: int, trigger_type: str
    ) -> Trigger | None:
        return (
            self.db.query(Trigger)
            .filter(
                Trigger.news_article_id == news_article_id,
                Trigger.trigger_type == trigger_type,
            )
            .first()
        )

    def list_event_candidates(
        self,
        *,
        company_id: int,
        trigger_type: str,
        event_date: datetime,
        window_days: int,
    ) -> list[Trigger]:
        return (
            self.db.query(Trigger)
            .filter(
                Trigger.company_id == company_id,
                Trigger.trigger_type == trigger_type,
                Trigger.event_date >= event_date - timedelta(days=window_days),
                Trigger.event_date <= event_date + timedelta(days=window_days),
            )
            .order_by(Trigger.id.asc())
            .all()
        )

    def create(self, trigger: Trigger) -> Trigger:
        self.db.add(trigger)
        self.db.flush()

        return trigger
