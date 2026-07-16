from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailRevisionRead(BaseModel):
    id: int
    email_draft_id: int
    subject: str
    body: str
    editor_name: str | None
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
