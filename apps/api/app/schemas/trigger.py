from datetime import datetime
from typing import Any

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TriggerExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article_ids: list[int] | None = Field(
        default=None, min_length=1, max_length=100
    )
    company_id: int | None = Field(default=None, ge=1)
    status: Literal["pending", "processed", "no_trigger", "failed"] = "pending"
    extraction_version: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=100, ge=1, le=500)

    @field_validator("article_ids")
    @classmethod
    def unique_article_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError("article_ids must be unique")
        return value


class TriggerBatchErrorRead(BaseModel):
    article_id: int
    category: str
    retryable: bool


class TriggerBatchReportRead(BaseModel):
    status: Literal["ok", "partial", "failed"]
    requested: int
    selected: int
    succeeded: int
    failed: int
    no_trigger: int
    triggers_created: int
    triggers_merged: int
    fallback_count: int
    errors: list[TriggerBatchErrorRead] | tuple[TriggerBatchErrorRead, ...]

    model_config = ConfigDict(from_attributes=True)


class TriggerRead(BaseModel):
    id: int
    company_id: int
    news_article_id: int | None
    trigger_type: str
    title: str
    description: str | None
    confidence_score: float
    detected_at: datetime
    evidence_refs: list[dict[str, Any]]
    event_date: datetime | None
    evidence_sentence: str | None
    extraction_method: str
    deduplication_key: str
    is_negative: bool
    review_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
