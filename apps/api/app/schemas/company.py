from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    domain: str | None = Field(default=None, max_length=255)
    sector: str = Field(min_length=1, max_length=255)
    country: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    mandate_id: int | None = Field(default=None, ge=1)


class CompanyRead(BaseModel):
    id: int
    name: str
    website: str | None
    domain: str | None
    sector: str
    country: str
    description: str | None
    status: str
    source: str | None
    source_url: str | None
    external_id: str | None
    extra_data: dict[str, Any]
    mandate_id: int | None
    pipeline_stage: str
    owner: str | None
    source_channel: str | None
    first_seen_at: datetime
    reviewed_at: datetime | None
    contacted_at: datetime | None
    next_action: str | None
    next_action_due_at: datetime | None
    pass_reason: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
