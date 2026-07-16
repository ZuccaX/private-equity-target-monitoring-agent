from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.agent_run import AgentRunDetail, AgentRunSummary
from app.schemas.agent_run_step import AgentRunStepRead
from app.services.agent_run_service import AgentRunService
from app.services.agent_run_step_service import AgentRunStepService


router = APIRouter(
    prefix="/api/agent-runs",
    tags=["agent-runs"],
)


@router.get("/{agent_run_id}/steps", response_model=list[AgentRunStepRead])
def list_agent_run_steps(
    agent_run_id: int,
    db: Session = Depends(get_db),
) -> list[AgentRunStepRead]:
    try:
        return AgentRunStepService(db).list_steps(agent_run_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("", response_model=list[AgentRunSummary])
def list_agent_runs(
    db: Session = Depends(get_db),
) -> list[AgentRunSummary]:
    service = AgentRunService(db)

    return service.list_agent_runs()


@router.post("/{company_id}", response_model=AgentRunDetail)
def run_agent_for_company(
    company_id: int,
    db: Session = Depends(get_db),
) -> AgentRunDetail:
    service = AgentRunService(db)

    try:
        return service.run_agent_for_company(company_id)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
