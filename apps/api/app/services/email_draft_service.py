from sqlalchemy.orm import Session

from app.models.approval import Approval
from app.models.audit_log import AuditLog
from app.models.email_revision import EmailRevision
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.email_draft_repository import EmailDraftRepository
from app.repositories.email_revision_repository import EmailRevisionRepository
from app.schemas.email_revision import EmailRevisionRead
from app.schemas.email_draft import EmailDraftRead, EmailDraftUpdate


class EmailDraftService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.email_draft_repository = EmailDraftRepository(db)
        self.approval_repository = ApprovalRepository(db)
        self.audit_log_repository = AuditLogRepository(db)
        self.email_revision_repository = EmailRevisionRepository(db)

    def list_drafts(self) -> list[EmailDraftRead]:
        drafts = self.email_draft_repository.list_all()

        return [
            EmailDraftRead.model_validate(draft)
            for draft in drafts
        ]

    def update_draft(
        self,
        draft_id: int,
        request: EmailDraftUpdate,
    ) -> EmailDraftRead:
        draft = self.email_draft_repository.get_by_id(draft_id)

        if draft is None:
            raise ValueError(f"Email draft not found: {draft_id}")

        before_data = {
            "subject": draft.subject,
            "body": draft.body,
            "status": draft.status,
        }

        try:
            content_changed = request.subject is not None or request.body is not None
            if content_changed:
                self.email_revision_repository.create(
                    EmailRevision(
                        email_draft_id=draft.id,
                        subject=draft.subject,
                        body=draft.body,
                        editor_name=request.reviewer_name,
                        comment=request.comment,
                    )
                )

            if request.subject is not None:
                draft.subject = request.subject

            if request.body is not None:
                draft.body = request.body

            if request.status is not None:
                draft.status = request.status

                if request.status in {
                    "approved",
                    "rejected",
                    "revision_requested",
                }:
                    self.approval_repository.create(
                        Approval(
                            email_draft_id=draft.id,
                            decision=request.status,
                            comment=request.comment,
                            reviewer_name=request.reviewer_name,
                            reviewer_role=request.reviewer_role,
                        )
                    )

            after_data = {
                "subject": draft.subject,
                "body": draft.body,
                "status": draft.status,
            }
            self.audit_log_repository.create(
                AuditLog(
                    entity_type="email_draft",
                    entity_id=draft.id,
                    action="updated",
                    actor_type="user",
                    actor_name=request.reviewer_name,
                    before_data=before_data,
                    after_data=after_data,
                )
            )
            self.db.commit()
            self.db.refresh(draft)

            return EmailDraftRead.model_validate(draft)

        except Exception:
            self.db.rollback()
            raise

    def list_revisions(self, draft_id: int) -> list[EmailRevisionRead]:
        if self.email_draft_repository.get_by_id(draft_id) is None:
            raise ValueError(f"Email draft not found: {draft_id}")
        return [
            EmailRevisionRead.model_validate(revision)
            for revision in self.email_revision_repository.list_by_draft_id(draft_id)
        ]
