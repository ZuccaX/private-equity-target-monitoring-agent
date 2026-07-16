import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun
from app.models.agent_run_step import AgentRunStep
from app.models.company import Company
from app.models.email_draft import EmailDraft
from app.models.email_revision import EmailRevision
from app.schemas.email_draft import EmailDraftUpdate
from app.services.agent_run_service import AgentRunService
from app.services.email_draft_service import EmailDraftService


def test_agent_failure_persists_safe_run_step_metadata(
    db_session: Session,
) -> None:
    company = Company(
        name="Failing Workflow Company",
        sector="Software",
        country="France",
        status="active",
        extra_data={},
    )
    db_session.add(company)
    db_session.commit()
    service = AgentRunService(db_session)

    def fail_workflow(**_kwargs: object) -> None:
        raise RuntimeError("provider-token-must-not-be-persisted")

    service.origination_workflow.run = fail_workflow  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="provider-token"):
        service.run_agent_for_company(company.id)

    run = db_session.scalars(select(AgentRun)).one()
    steps = db_session.scalars(
        select(AgentRunStep).order_by(AgentRunStep.id)
    ).all()
    assert run.status == "failed"
    assert run.error_message == "Workflow execution failed"
    assert [step.status for step in steps] == ["completed", "failed"]
    assert steps[-1].error_code == "RuntimeError"
    assert steps[-1].error_message == "Workflow execution failed"
    assert "provider-token" not in (run.error_message or "")


def test_draft_revision_rolls_back_with_audit_failure(
    db_session: Session,
) -> None:
    company = Company(
        name="Revision Company",
        sector="Software",
        country="France",
        status="active",
        extra_data={},
    )
    db_session.add(company)
    db_session.flush()
    run = AgentRun(
        company_id=company.id,
        run_type="test",
        status="completed",
        workflow_version="test",
        input_snapshot={},
    )
    db_session.add(run)
    db_session.flush()
    draft = EmailDraft(
        agent_run_id=run.id,
        company_id=company.id,
        subject="Original subject",
        body="Original body",
        status="pending_approval",
        tone="professional",
        generated_by="test",
        evidence_refs=[],
    )
    db_session.add(draft)
    db_session.commit()
    service = EmailDraftService(db_session)

    def fail_audit(_audit_log: object) -> None:
        raise RuntimeError("audit storage failed")

    service.audit_log_repository.create = fail_audit  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="audit storage failed"):
        service.update_draft(
            draft.id,
            EmailDraftUpdate(subject="Changed subject", reviewer_name="Reviewer"),
        )

    db_session.refresh(draft)
    assert draft.subject == "Original subject"
    assert db_session.scalars(select(EmailRevision)).all() == []
