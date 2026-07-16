from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.company import CompanyRead
from app.schemas.pipeline import CompanyPipelineUpdate
from app.services.pipeline_service import PipelineService


router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("", response_model=list[CompanyRead])
def list_pipeline(db: Session = Depends(get_db)) -> list[CompanyRead]:
    return PipelineService(db).list_pipeline()


@router.patch("/companies/{company_id}", response_model=CompanyRead)
def update_company_pipeline(
    company_id: int,
    request: CompanyPipelineUpdate,
    db: Session = Depends(get_db),
) -> CompanyRead:
    try:
        return PipelineService(db).update_company_pipeline(company_id, request)
    except ValueError as error:
        raise NotFoundError(str(error)) from error
