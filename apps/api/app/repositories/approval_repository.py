from sqlalchemy.orm import Session

from app.models.approval import Approval


class ApprovalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, approval: Approval) -> Approval:
        self.db.add(approval)
        self.db.flush()

        return approval