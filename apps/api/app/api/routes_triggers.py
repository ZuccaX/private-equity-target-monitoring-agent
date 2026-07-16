from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.schemas.trigger import (
    TriggerBatchReportRead,
    TriggerExtractRequest,
    TriggerRead,
)
from app.services.trigger_batch_service import TriggerBatchService
from app.services.trigger_service import TriggerService


router = APIRouter(
    prefix="/api/triggers",
    tags=["triggers"],
)


@router.get("", response_model=list[TriggerRead])
def list_triggers(
    company_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[TriggerRead]:
    service = TriggerService(db)

    return service.list_triggers(company_id=company_id)


@router.post("/extract", response_model=TriggerBatchReportRead)
def extract_triggers(
    request: TriggerExtractRequest,
    db: Session = Depends(get_db),
) -> dict:
    version = request.extraction_version or settings.trigger_extraction_version
    if version != settings.trigger_extraction_version:
        raise HTTPException(
            status_code=422,
            detail="Extraction version must match the configured version.",
        )
    report = TriggerBatchService(
        db,
        version=version,
    ).process(
        article_ids=request.article_ids,
        company_id=request.company_id,
        status=request.status,
        limit=request.limit,
    )
    if report.status == "failed":
        raise HTTPException(
            status_code=503, detail="All selected articles failed extraction."
        )
    return asdict(report)
