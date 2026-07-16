from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, audit_log: AuditLog) -> AuditLog:
        self.db.add(audit_log)
        self.db.flush()

        return audit_log

    def list_all(
        self,
        *,
        entity_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        query = self.db.query(AuditLog)
        if entity_type is not None:
            query = query.filter(AuditLog.entity_type == entity_type)
        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
