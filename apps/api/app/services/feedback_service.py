from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import FeedbackCreate, FeedbackRead


class FeedbackService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = FeedbackRepository(db)
        self.agent_run_repository = AgentRunRepository(db)
        self.company_repository = CompanyRepository(db)

    def list_feedback(
        self,
        *,
        agent_run_id: int | None,
        company_id: int | None,
        offset: int,
        limit: int,
    ) -> list[FeedbackRead]:
        return [
            FeedbackRead.model_validate(item)
            for item in self.repository.list_all(
                agent_run_id=agent_run_id,
                company_id=company_id,
                offset=offset,
                limit=limit,
            )
        ]

    def create_feedback(self, request: FeedbackCreate) -> FeedbackRead:
        if request.agent_run_id is not None and self.agent_run_repository.get_by_id(
            request.agent_run_id
        ) is None:
            raise ValueError(f"Agent run not found: {request.agent_run_id}")
        if request.company_id is not None and self.company_repository.get_by_id(
            request.company_id
        ) is None:
            raise ValueError(f"Company not found: {request.company_id}")

        item = Feedback(**request.model_dump())
        try:
            self.repository.create(item)
            self.db.commit()
            self.db.refresh(item)
            return FeedbackRead.model_validate(item)
        except Exception:
            self.db.rollback()
            raise
