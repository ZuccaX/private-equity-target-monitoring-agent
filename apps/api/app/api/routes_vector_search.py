from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vector_search import (
    VectorSearchRequest,
    VectorSearchResponse,
)
from app.services.vector_search_service import (
    VectorSearchService,
)


router = APIRouter(
    prefix="/api/vector",
    tags=["vector-search"],
)


@router.post(
    "/search",
    response_model=VectorSearchResponse,
)
def search_document_chunks(
    request: VectorSearchRequest,
    db: Session = Depends(get_db),
) -> VectorSearchResponse:
    service = VectorSearchService(db)

    try:
        return service.search(request)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error