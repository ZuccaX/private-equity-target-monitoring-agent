from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun
from app.models.company import Company
from app.models.email_draft import EmailDraft
from app.models.news_article import NewsArticle
from app.models.priority_score import PriorityScore
from app.models.trigger import Trigger
from app.schemas.dashboard import DashboardSummaryRead


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_summary(self) -> DashboardSummaryRead:
        total_companies = (
            self.db.query(func.count(Company.id))
            .filter(Company.deleted_at.is_(None))
            .scalar()
            or 0
        )

        total_news_articles = (
            self.db.query(func.count(NewsArticle.id)).scalar()
            or 0
        )

        total_triggers = (
            self.db.query(func.count(Trigger.id)).scalar()
            or 0
        )

        total_agent_runs = (
            self.db.query(func.count(AgentRun.id)).scalar()
            or 0
        )

        completed_agent_runs = (
            self.db.query(func.count(AgentRun.id))
            .filter(AgentRun.status == "completed")
            .scalar()
            or 0
        )

        failed_agent_runs = (
            self.db.query(func.count(AgentRun.id))
            .filter(AgentRun.status == "failed")
            .scalar()
            or 0
        )

        pending_drafts = (
            self.db.query(func.count(EmailDraft.id))
            .filter(
                EmailDraft.status == "pending_approval",
                EmailDraft.deleted_at.is_(None),
            )
            .scalar()
            or 0
        )

        approved_drafts = (
            self.db.query(func.count(EmailDraft.id))
            .filter(
                EmailDraft.status == "approved",
                EmailDraft.deleted_at.is_(None),
            )
            .scalar()
            or 0
        )

        average_score_value = (
            self.db.query(
                func.avg(PriorityScore.overall_score)
            )
            .scalar()
        )

        average_priority_score = (
            round(float(average_score_value), 1)
            if average_score_value is not None
            else None
        )

        return DashboardSummaryRead(
            total_companies=int(total_companies),
            total_news_articles=int(total_news_articles),
            total_triggers=int(total_triggers),
            total_agent_runs=int(total_agent_runs),
            completed_agent_runs=int(completed_agent_runs),
            failed_agent_runs=int(failed_agent_runs),
            pending_drafts=int(pending_drafts),
            approved_drafts=int(approved_drafts),
            average_priority_score=average_priority_score,
        )