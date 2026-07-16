from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes_health import get_integration_health
from app.core.database import get_db
from app.schemas.integration import IntegrationHealthRead


router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get(
    "/health",
    response_model=IntegrationHealthRead,
    summary="Report configured integration health",
)
def integration_health(
    db: Session = Depends(get_db),
) -> IntegrationHealthRead:
    return get_integration_health(db)
