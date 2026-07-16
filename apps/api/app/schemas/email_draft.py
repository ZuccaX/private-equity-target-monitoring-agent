from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


EmailDraftStatus = Literal[
    "drafted",
    "pending_approval",
    "approved",
    "rejected",
    "revision_requested",
    "sent_simulated",
]


class EmailDraftRead(BaseModel):
    id: int
    agent_run_id: int
    company_id: int
    subject: str
    body: str
    status: str
    tone: str
    recipient_name: str | None
    recipient_email: str | None
    generated_by: str
    model_name: str | None
    prompt_version: str | None
    evidence_refs: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class EmailDraftUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None
    status: EmailDraftStatus | None = None
    comment: str | None = None
    reviewer_name: str | None = "Demo Reviewer"
    reviewer_role: str | None = "Investment Analyst"