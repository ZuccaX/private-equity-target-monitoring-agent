from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.core.database import get_db
from app.core.exceptions import DependencyUnavailableError
from app.schemas.integration import (
    IntegrationComponentHealth,
    IntegrationHealthRead,
)
from app.services.embeddings.registry import EmbeddingProviderRegistry


router = APIRouter(tags=["health"])


def get_embedding_health(
    *,
    configured: Settings = settings,
    registry: EmbeddingProviderRegistry | None = None,
) -> IntegrationComponentHealth:
    resolution = (registry or EmbeddingProviderRegistry(configured)).resolve()
    requested = resolution.requested_provider
    effective = resolution.effective_provider
    return IntegrationComponentHealth(
        name="embeddings",
        status="degraded" if resolution.fallback_category else "ok",
        mode=(requested if requested == effective else f"{requested}->{effective}"),
        detail=resolution.fallback_category,
    )


@router.get("/health", summary="Process liveness")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready", summary="Database readiness")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise DependencyUnavailableError("Database is unavailable") from error
    return {"status": "ok", "database": "available"}


def get_integration_health(db: Session) -> IntegrationHealthRead:
    components: list[IntegrationComponentHealth] = []
    try:
        db.execute(text("SELECT 1"))
        components.append(
            IntegrationComponentHealth(
                name="database", status="ok", mode="postgresql"
            )
        )
    except SQLAlchemyError:
        components.append(
            IntegrationComponentHealth(
                name="database",
                status="unavailable",
                mode="postgresql",
                detail="Database connection failed",
            )
        )

    components.extend(
        [
            IntegrationComponentHealth(
                name="crm",
                status="ok",
                mode=settings.crm_integration_mode,
                detail="Repository adapter configured",
            ),
            IntegrationComponentHealth(
                name="documents",
                status="ok",
                mode=settings.document_integration_mode,
                detail="Repository adapter configured",
            ),
            get_embedding_health(),
        ]
    )
    overall = (
        "ok"
        if all(component.status == "ok" for component in components)
        else "degraded"
    )
    return IntegrationHealthRead(status=overall, components=components)
