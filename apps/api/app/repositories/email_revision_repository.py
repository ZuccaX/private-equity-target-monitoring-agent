from sqlalchemy.orm import Session

from app.models.email_revision import EmailRevision


class EmailRevisionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_draft_id(self, draft_id: int) -> list[EmailRevision]:
        return self.db.query(EmailRevision).filter(
            EmailRevision.email_draft_id == draft_id
        ).order_by(EmailRevision.created_at.desc()).all()

    def create(self, revision: EmailRevision) -> EmailRevision:
        self.db.add(revision)
        self.db.flush()
        return revision
