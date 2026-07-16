from pydantic import BaseModel


class DashboardSummaryRead(BaseModel):
    total_companies: int
    total_news_articles: int
    total_triggers: int
    total_agent_runs: int
    completed_agent_runs: int
    failed_agent_runs: int
    pending_drafts: int
    approved_drafts: int
    average_priority_score: float | None