from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ContactRead(BaseModel):
    id: int
    company_id: int
    full_name: str
    job_title: str | None
    email: str | None
    phone: str | None
    relationship_strength: int
    source: str
    external_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CRMInteractionRead(BaseModel):
    id: int
    company_id: int
    contact_id: int | None
    interaction_type: str
    direction: str
    summary: str
    occurred_at: datetime
    sentiment_score: float
    source: str
    external_id: str | None
    raw_payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)