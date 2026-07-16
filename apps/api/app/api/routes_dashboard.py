from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard import DashboardSummaryRead
from app.services.dashboard_service import DashboardService


router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummaryRead,
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
) -> DashboardSummaryRead:
    service = DashboardService(db)

    return service.get_summary()