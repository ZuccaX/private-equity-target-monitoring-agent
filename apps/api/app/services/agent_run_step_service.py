from sqlalchemy.orm import Session

from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.agent_run_step_repository import AgentRunStepRepository
from app.schemas.agent_run_step import AgentRunStepRead


class AgentRunStepService:
    def __init__(self, db: Session) -> None:
        self.run_repository = AgentRunRepository(db)
        self.step_repository = AgentRunStepRepository(db)

    def list_steps(self, agent_run_id: int) -> list[AgentRunStepRead]:
        if self.run_repository.get_by_id(agent_run_id) is None:
            raise ValueError(f"Agent run not found: {agent_run_id}")
        return [
            AgentRunStepRead.model_validate(step)
            for step in self.step_repository.list_by_agent_run_id(agent_run_id)
        ]
