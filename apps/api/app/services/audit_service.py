from sqlalchemy.orm import Session

from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit import AuditLogRead


class AuditService:
    def __init__(self, db: Session) -> None:
        self.repository = AuditLogRepository(db)

    def list_audit_logs(
        self,
        *,
        entity_type: str | None,
        offset: int,
        limit: int,
    ) -> list[AuditLogRead]:
        return [
            AuditLogRead.model_validate(item)
            for item in self.repository.list_all(
                entity_type=entity_type,
                offset=offset,
                limit=limit,
            )
        ]
