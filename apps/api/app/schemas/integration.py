from typing import Literal

from pydantic import BaseModel


HealthStatus = Literal["ok", "degraded", "unavailable", "not_configured"]


class IntegrationComponentHealth(BaseModel):
    name: str
    status: HealthStatus
    mode: str
    detail: str | None = None


class IntegrationHealthRead(BaseModel):
    status: HealthStatus
    components: list[IntegrationComponentHealth]
