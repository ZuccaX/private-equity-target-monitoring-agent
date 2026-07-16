from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun


class AgentRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[AgentRun]:
        return (
            self.db.query(AgentRun)
            .order_by(AgentRun.created_at.desc())
            .all()
        )

    def get_by_id(self, agent_run_id: int) -> AgentRun | None:
        return (
            self.db.query(AgentRun)
            .filter(AgentRun.id == agent_run_id)
            .first()
        )

    def create(self, agent_run: AgentRun) -> AgentRun:
        self.db.add(agent_run)
        self.db.flush()

        return agent_run