from sqlalchemy.orm import Session

from app.models.agent_run_step import AgentRunStep


class AgentRunStepRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_agent_run_id(self, agent_run_id: int) -> list[AgentRunStep]:
        return self.db.query(AgentRunStep).filter(
            AgentRunStep.agent_run_id == agent_run_id
        ).order_by(AgentRunStep.id.asc()).all()

    def get_by_id(self, step_id: int) -> AgentRunStep | None:
        return self.db.get(AgentRunStep, step_id)

    def create(self, step: AgentRunStep) -> AgentRunStep:
        self.db.add(step)
        self.db.flush()
        return step
