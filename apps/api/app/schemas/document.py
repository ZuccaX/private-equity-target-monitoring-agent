from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DocumentSummaryRead(BaseModel):
    id: int
    company_id: int
    title: str
    file_name: str
    document_type: str
    source_system: str
    source_path: str | None
    mime_type: str | None
    uploaded_at: datetime | None
    ingested_at: datetime
    external_id: str | None
    extra_data: dict[str, Any]
    content_hash: str | None
    file_version: str | None
    sync_status: str
    last_synced_at: datetime | None
    indexed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(DocumentSummaryRead):
    content_text: str | None
