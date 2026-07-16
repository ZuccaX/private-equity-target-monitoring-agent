from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService


router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    entity_type: str | None = Query(default=None, max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    return AuditService(db).list_audit_logs(
        entity_type=entity_type, offset=offset, limit=limit
    )
