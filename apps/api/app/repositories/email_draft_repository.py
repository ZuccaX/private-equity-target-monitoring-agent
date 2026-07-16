from sqlalchemy.orm import Session

from app.models.email_draft import EmailDraft


class EmailDraftRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[EmailDraft]:
        return (
            self.db.query(EmailDraft)
            .filter(EmailDraft.deleted_at.is_(None))
            .order_by(EmailDraft.created_at.desc())
            .all()
        )

    def get_by_id(self, draft_id: int) -> EmailDraft | None:
        return (
            self.db.query(EmailDraft)
            .filter(
                EmailDraft.id == draft_id,
                EmailDraft.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_agent_run_id(self, agent_run_id: int) -> EmailDraft | None:
        return (
            self.db.query(EmailDraft)
            .filter(
                EmailDraft.agent_run_id == agent_run_id,
                EmailDraft.deleted_at.is_(None),
            )
            .first()
        )

    def create(self, email_draft: EmailDraft) -> EmailDraft:
        self.db.add(email_draft)
        self.db.flush()

        return email_draft