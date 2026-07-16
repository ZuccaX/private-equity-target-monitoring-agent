from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: int
    entity_type: str
    entity_id: int | None
    action: str
    actor_type: str
    actor_name: str | None
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
