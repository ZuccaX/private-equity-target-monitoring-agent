from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

class NewsSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_ids: list[str] | None = Field(default=None, min_length=1, max_length=50)
    extract_triggers: bool = True
    max_items_per_source: int = Field(default=100, ge=1, le=500)

    @field_validator("source_ids")
    @classmethod
    def unique_source_ids(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError("source_ids must be unique")
        return value


class NewsArticleRead(BaseModel):
    id: int
    company_id: int
    title: str
    summary: str | None
    url: str | None
    source: str
    published_at: datetime | None
    ingested_at: datetime
    raw_payload: dict[str, Any]
    canonical_url: str | None
    content_hash: str | None
    language: str
    source_reliability: float
    company_match_confidence: float
    ingestion_status: str
    external_id: str | None
    trigger_extraction_status: str
    trigger_extracted_at: datetime | None
    trigger_extraction_version: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
