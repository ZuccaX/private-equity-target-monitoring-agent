from sqlalchemy.orm import Session

from app.models.feedback import Feedback


class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(
        self,
        *,
        agent_run_id: int | None = None,
        company_id: int | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Feedback]:
        query = self.db.query(Feedback)
        if agent_run_id is not None:
            query = query.filter(Feedback.agent_run_id == agent_run_id)
        if company_id is not None:
            query = query.filter(Feedback.company_id == company_id)
        return query.order_by(Feedback.created_at.desc()).offset(offset).limit(limit).all()

    def create(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        self.db.flush()
        return feedback
