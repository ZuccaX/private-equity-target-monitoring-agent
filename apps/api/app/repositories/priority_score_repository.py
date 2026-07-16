from sqlalchemy.orm import Session

from app.models.priority_score import PriorityScore


class PriorityScoreRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_agent_run_id(self, agent_run_id: int) -> PriorityScore | None:
        return (
            self.db.query(PriorityScore)
            .filter(PriorityScore.agent_run_id == agent_run_id)
            .first()
        )

    def create(self, priority_score: PriorityScore) -> PriorityScore:
        self.db.add(priority_score)
        self.db.flush()

        return priority_score