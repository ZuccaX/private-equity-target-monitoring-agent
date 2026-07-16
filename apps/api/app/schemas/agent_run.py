from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.email_draft import EmailDraftRead
from app.schemas.priority_score import PriorityScoreRead


class AgentRunRead(BaseModel):
    id: int
    company_id: int
    run_type: str
    status: str
    workflow_version: str
    model_name: str | None
    prompt_version: str | None
    input_snapshot: dict[str, Any]
    output_summary: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunSummary(BaseModel):
    id: int
    company_id: int
    company_name: str
    run_type: str
    status: str
    overall_score: int | None
    email_draft_id: int | None
    email_draft_status: str | None
    completed_at: datetime | None
    created_at: datetime


class AgentRunDetail(BaseModel):
    agent_run: AgentRunRead
    priority_score: PriorityScoreRead | None
    email_draft: EmailDraftRead | None