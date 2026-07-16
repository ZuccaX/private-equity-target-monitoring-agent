from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


FeedbackType = Literal[
    "rag_relevance",
    "trigger_accuracy",
    "score_quality",
    "recommended_action",
    "email_quality",
    "overall_run",
]


class FeedbackCreate(BaseModel):
    agent_run_id: int | None = Field(default=None, ge=1)
    company_id: int | None = Field(default=None, ge=1)
    feedback_type: FeedbackType
    rating: int | None = Field(default=None, ge=1, le=5)
    is_helpful: bool | None = None
    comment: str | None = Field(default=None, max_length=5000)
    submitted_by: str | None = Field(default=None, max_length=255)
    extra_data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_feedback_value(self) -> Self:
        if self.rating is None and self.is_helpful is None and not self.comment:
            raise ValueError(
                "At least one of rating, is_helpful, or comment is required."
            )
        return self


class FeedbackRead(FeedbackCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
