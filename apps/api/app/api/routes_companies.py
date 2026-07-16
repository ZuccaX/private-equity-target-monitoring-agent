from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.company import CompanyCreate, CompanyRead
from app.services.company_service import CompanyService


router = APIRouter(
    prefix="/api/companies",
    tags=["companies"],
)


@router.get("", response_model=list[CompanyRead])
def list_companies(
    db: Session = Depends(get_db),
) -> list[CompanyRead]:
    service = CompanyService(db)

    return service.list_companies()


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(db)

    try:
        return service.get_company(company_id)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.post("", response_model=CompanyRead)
def create_company(
    request: CompanyCreate,
    db: Session = Depends(get_db),
) -> CompanyRead:
    service = CompanyService(db)

    try:
        return service.create_company(request)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error