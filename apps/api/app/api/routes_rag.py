from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vector_search import (
    RAGRetrievalRequest,
    RAGRetrievalResponse,
)
from app.services.rag_retrieval_service import (
    RAGRetrievalService,
)


router = APIRouter(
    prefix="/api/rag",
    tags=["rag"],
)


@router.post(
    "/retrieve",
    response_model=RAGRetrievalResponse,
)
def retrieve_rag_context(
    request: RAGRetrievalRequest,
    db: Session = Depends(get_db),
) -> RAGRetrievalResponse:
    service = RAGRetrievalService(db)

    try:
        return service.retrieve(request)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
