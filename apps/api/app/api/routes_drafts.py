from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.email_draft import EmailDraftRead, EmailDraftUpdate
from app.schemas.email_revision import EmailRevisionRead
from app.services.email_draft_service import EmailDraftService


router = APIRouter(
    prefix="/api/drafts",
    tags=["drafts"],
)


@router.get("/{draft_id}/revisions", response_model=list[EmailRevisionRead])
def list_draft_revisions(
    draft_id: int,
    db: Session = Depends(get_db),
) -> list[EmailRevisionRead]:
    try:
        return EmailDraftService(db).list_revisions(draft_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("", response_model=list[EmailDraftRead])
def list_drafts(
    db: Session = Depends(get_db),
) -> list[EmailDraftRead]:
    service = EmailDraftService(db)

    return service.list_drafts()


@router.patch("/{draft_id}", response_model=EmailDraftRead)
def update_draft(
    draft_id: int,
    request: EmailDraftUpdate,
    db: Session = Depends(get_db),
) -> EmailDraftRead:
    service = EmailDraftService(db)

    try:
        return service.update_draft(
            draft_id=draft_id,
            request=request,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
