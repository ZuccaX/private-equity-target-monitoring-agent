from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.mandate import (
    InvestmentMandateCreate,
    InvestmentMandateRead,
    InvestmentMandateUpdate,
)
from app.services.investment_mandate_service import InvestmentMandateService


router = APIRouter(prefix="/api/mandates", tags=["mandates"])


@router.get("", response_model=list[InvestmentMandateRead])
def list_mandates(
    active_only: bool = False,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[InvestmentMandateRead]:
    return InvestmentMandateService(db).list_mandates(
        active_only=active_only, offset=offset, limit=limit
    )


@router.get("/{mandate_id}", response_model=InvestmentMandateRead)
def get_mandate(
    mandate_id: int, db: Session = Depends(get_db)
) -> InvestmentMandateRead:
    try:
        return InvestmentMandateService(db).get_mandate(mandate_id)
    except ValueError as error:
        raise NotFoundError(str(error)) from error


@router.post(
    "",
    response_model=InvestmentMandateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_mandate(
    request: InvestmentMandateCreate,
    db: Session = Depends(get_db),
) -> InvestmentMandateRead:
    try:
        return InvestmentMandateService(db).create_mandate(request)
    except ValueError as error:
        raise ConflictError(str(error)) from error


@router.patch("/{mandate_id}", response_model=InvestmentMandateRead)
def update_mandate(
    mandate_id: int,
    request: InvestmentMandateUpdate,
    db: Session = Depends(get_db),
) -> InvestmentMandateRead:
    try:
        return InvestmentMandateService(db).update_mandate(mandate_id, request)
    except ValueError as error:
        if "not found" in str(error).lower():
            raise NotFoundError(str(error)) from error
        raise ConflictError(str(error)) from error
