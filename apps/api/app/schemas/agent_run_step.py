from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentRunStepRead(BaseModel):
    id: int
    agent_run_id: int
    node_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    input_summary: str | None
    output_summary: str | None
    fallback_used: bool
    fallback_reason: str | None
    error_code: str | None
    error_message: str | None
    extra_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
