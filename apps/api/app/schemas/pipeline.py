from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PipelineStage = Literal[
    "sourced",
    "monitoring",
    "triggered",
    "screening",
    "qualified",
    "contacted",
    "in_conversation",
    "passed",
    "archived",
]


class CompanyPipelineUpdate(BaseModel):
    mandate_id: int | None = Field(default=None, ge=1)
    pipeline_stage: PipelineStage | None = None
    owner: str | None = Field(default=None, max_length=255)
    source_channel: str | None = Field(default=None, max_length=100)
    reviewed_at: datetime | None = None
    contacted_at: datetime | None = None
    next_action: str | None = Field(default=None, max_length=100)
    next_action_due_at: datetime | None = None
    pass_reason: str | None = Field(default=None, max_length=5000)
