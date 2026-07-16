from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.crm import ContactRead, CRMInteractionRead
from app.services.crm_service import CRMService


router = APIRouter(
    prefix="/api/crm",
    tags=["crm"],
)


@router.get(
    "/contacts",
    response_model=list[ContactRead],
)
def list_contacts(
    company_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[ContactRead]:
    service = CRMService(db)

    return service.list_contacts(company_id=company_id)


@router.get(
    "/interactions",
    response_model=list[CRMInteractionRead],
)
def list_interactions(
    company_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[CRMInteractionRead]:
    service = CRMService(db)

    return service.list_interactions(company_id=company_id)