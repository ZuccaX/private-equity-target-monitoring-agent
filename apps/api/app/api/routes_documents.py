from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.document import DocumentRead, DocumentSummaryRead
from app.services.document_service import DocumentService


router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)


@router.get(
    "",
    response_model=list[DocumentSummaryRead],
)
def list_documents(
    company_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[DocumentSummaryRead]:
    service = DocumentService(db)

    return service.list_documents(
        company_id=company_id
    )


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> DocumentRead:
    service = DocumentService(db)

    try:
        return service.get_document(document_id)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error