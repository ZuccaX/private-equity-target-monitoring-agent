from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.services.feedback_service import FeedbackService


router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.get("", response_model=list[FeedbackRead])
def list_feedback(
    agent_run_id: int | None = Query(default=None, ge=1),
    company_id: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[FeedbackRead]:
    return FeedbackService(db).list_feedback(
        agent_run_id=agent_run_id,
        company_id=company_id,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def create_feedback(
    request: FeedbackCreate,
    db: Session = Depends(get_db),
) -> FeedbackRead:
    try:
        return FeedbackService(db).create_feedback(request)
    except ValueError as error:
        raise NotFoundError(str(error)) from error
