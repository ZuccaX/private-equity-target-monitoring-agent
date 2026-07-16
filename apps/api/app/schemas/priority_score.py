from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PriorityScoreRead(BaseModel):
    id: int
    agent_run_id: int
    company_id: int
    overall_score: int
    score_version: str
    sector_fit_score: int
    trigger_score: int
    relationship_score: int
    timing_score: int
    risk_score: int
    reasons: list[str]
    evidence_refs: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)