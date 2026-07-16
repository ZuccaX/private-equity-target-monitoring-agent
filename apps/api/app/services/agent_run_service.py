from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.origination_workflow import OriginationWorkflow
from app.models.agent_run import AgentRun
from app.models.agent_run_step import AgentRunStep
from app.models.audit_log import AuditLog
from app.models.email_draft import EmailDraft
from app.models.priority_score import PriorityScore
from app.repositories.agent_run_repository import (
    AgentRunRepository,
)
from app.repositories.agent_run_step_repository import AgentRunStepRepository
from app.repositories.audit_log_repository import (
    AuditLogRepository,
)
from app.repositories.company_repository import (
    CompanyRepository,
)
from app.repositories.contact_repository import (
    ContactRepository,
)
from app.repositories.crm_interaction_repository import (
    CRMInteractionRepository,
)
from app.repositories.email_draft_repository import (
    EmailDraftRepository,
)
from app.repositories.priority_score_repository import (
    PriorityScoreRepository,
)
from app.repositories.trigger_repository import (
    TriggerRepository,
)
from app.schemas.agent_run import (
    AgentRunDetail,
    AgentRunRead,
    AgentRunSummary,
)
from app.schemas.email_draft import EmailDraftRead
from app.schemas.priority_score import PriorityScoreRead


class AgentRunService:
    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

        self.company_repository = (
            CompanyRepository(db)
        )

        self.agent_run_repository = (
            AgentRunRepository(db)
        )

        self.agent_run_step_repository = AgentRunStepRepository(db)

        self.priority_score_repository = (
            PriorityScoreRepository(db)
        )

        self.email_draft_repository = (
            EmailDraftRepository(db)
        )

        self.audit_log_repository = (
            AuditLogRepository(db)
        )

        self.trigger_repository = (
            TriggerRepository(db)
        )

        self.contact_repository = (
            ContactRepository(db)
        )

        self.crm_interaction_repository = (
            CRMInteractionRepository(db)
        )

        self.origination_workflow = (
            OriginationWorkflow()
        )

    def list_agent_runs(
        self,
    ) -> list[AgentRunSummary]:
        agent_runs = (
            self.agent_run_repository
            .list_all()
        )

        summaries: list[AgentRunSummary] = []

        for agent_run in agent_runs:
            company = (
                self.company_repository
                .get_by_id(agent_run.company_id)
            )

            priority_score = (
                self.priority_score_repository
                .get_by_agent_run_id(
                    agent_run.id
                )
            )

            email_draft = (
                self.email_draft_repository
                .get_by_agent_run_id(
                    agent_run.id
                )
            )

            summaries.append(
                AgentRunSummary(
                    id=agent_run.id,
                    company_id=agent_run.company_id,
                    company_name=(
                        company.name
                        if company is not None
                        else "Unknown"
                    ),
                    run_type=agent_run.run_type,
                    status=agent_run.status,
                    overall_score=(
                        priority_score.overall_score
                        if priority_score is not None
                        else None
                    ),
                    email_draft_id=(
                        email_draft.id
                        if email_draft is not None
                        else None
                    ),
                    email_draft_status=(
                        email_draft.status
                        if email_draft is not None
                        else None
                    ),
                    completed_at=agent_run.completed_at,
                    created_at=agent_run.created_at,
                )
            )

        return summaries

    def run_agent_for_company(
        self,
        company_id: int,
    ) -> AgentRunDetail:
        company = (
            self.company_repository
            .get_by_id(company_id)
        )

        if company is None:
            raise ValueError(
                f"Company not found: {company_id}"
            )

        triggers = (
            self.trigger_repository
            .list_by_company_id(company.id)
        )

        contacts = (
            self.contact_repository
            .list_by_company_id(company.id)
        )

        interactions = (
            self.crm_interaction_repository
            .list_by_company_id(company.id)
        )

        now = datetime.now(timezone.utc)

        agent_run = AgentRun(
            company_id=company.id,
            run_type="full_workflow",
            status="running",
            workflow_version="v3-crm-trigger-aware",
            model_name="template-only",
            prompt_version="v3-crm-trigger-aware",
            input_snapshot={
                "company_id": company.id,
                "company_name": company.name,
                "sector": company.sector,
                "country": company.country,
                "status": company.status,
                "trigger_count": len(triggers),
                "trigger_ids": [
                    trigger.id
                    for trigger in triggers
                ],
                "contact_count": len(contacts),
                "contact_ids": [
                    contact.id
                    for contact in contacts
                ],
                "interaction_count": len(interactions),
                "interaction_ids": [
                    interaction.id
                    for interaction in interactions
                ],
            },
            started_at=now,
        )

        try:
            self.agent_run_repository.create(
                agent_run
            )

            self.db.commit()
            self.db.refresh(agent_run)

            context_completed_at = datetime.now(timezone.utc)
            self.agent_run_step_repository.create(
                AgentRunStep(
                    agent_run_id=agent_run.id,
                    node_name="load_context",
                    status="completed",
                    started_at=now,
                    completed_at=context_completed_at,
                    duration_ms=max(
                        0, int((context_completed_at - now).total_seconds() * 1000)
                    ),
                    input_summary=f"company_id={company.id}",
                    output_summary=(
                        f"triggers={len(triggers)}, contacts={len(contacts)}, "
                        f"interactions={len(interactions)}"
                    ),
                    extra_data={},
                )
            )
            workflow_step = self.agent_run_step_repository.create(
                AgentRunStep(
                    agent_run_id=agent_run.id,
                    node_name="execute_workflow",
                    status="running",
                    started_at=datetime.now(timezone.utc),
                    input_summary="Validated repository context",
                    extra_data={},
                )
            )
            self.db.commit()
            workflow_step_id = workflow_step.id

            workflow_result = (
                self.origination_workflow.run(
                    company=company,
                    triggers=triggers,
                    contacts=contacts,
                    interactions=interactions,
                )
            )

            workflow_completed_at = datetime.now(timezone.utc)
            workflow_step.status = "completed"
            workflow_step.completed_at = workflow_completed_at
            workflow_step.duration_ms = max(
                0,
                int(
                    (workflow_completed_at - workflow_step.started_at).total_seconds()
                    * 1000
                ),
            )
            workflow_step.output_summary = "Score and outreach draft generated"

            persist_step = self.agent_run_step_repository.create(
                AgentRunStep(
                    agent_run_id=agent_run.id,
                    node_name="persist_results",
                    status="running",
                    started_at=datetime.now(timezone.utc),
                    input_summary="Workflow output ready",
                    extra_data={},
                )
            )
            self.db.commit()
            persist_step_id = persist_step.id

            priority_score = PriorityScore(
                agent_run_id=agent_run.id,
                company_id=company.id,
                overall_score=(
                    workflow_result
                    .score
                    .overall_score
                ),
                score_version=(
                    workflow_result
                    .score
                    .score_version
                ),
                sector_fit_score=(
                    workflow_result
                    .score
                    .sector_fit_score
                ),
                trigger_score=(
                    workflow_result
                    .score
                    .trigger_score
                ),
                relationship_score=(
                    workflow_result
                    .score
                    .relationship_score
                ),
                timing_score=(
                    workflow_result
                    .score
                    .timing_score
                ),
                risk_score=(
                    workflow_result
                    .score
                    .risk_score
                ),
                reasons=(
                    workflow_result
                    .score
                    .reasons
                ),
                evidence_refs=(
                    workflow_result
                    .score
                    .evidence_refs
                ),
            )

            self.priority_score_repository.create(
                priority_score
            )

            email_draft = EmailDraft(
                agent_run_id=agent_run.id,
                company_id=company.id,
                subject=(
                    workflow_result
                    .email_draft
                    .subject
                ),
                body=(
                    workflow_result
                    .email_draft
                    .body
                ),
                status="pending_approval",
                tone=(
                    workflow_result
                    .email_draft
                    .tone
                ),
                recipient_name=(
                    workflow_result
                    .email_draft
                    .recipient_name
                ),
                recipient_email=(
                    workflow_result
                    .email_draft
                    .recipient_email
                ),
                generated_by=(
                    workflow_result
                    .email_draft
                    .generated_by
                ),
                model_name=(
                    workflow_result
                    .email_draft
                    .model_name
                ),
                prompt_version=(
                    workflow_result
                    .email_draft
                    .prompt_version
                ),
                evidence_refs=(
                    workflow_result
                    .email_draft
                    .evidence_refs
                ),
            )

            self.email_draft_repository.create(
                email_draft
            )

            agent_run.status = "completed"

            agent_run.completed_at = (
                datetime.now(timezone.utc)
            )

            agent_run.output_summary = (
                workflow_result.output_summary
            )

            audit_log = AuditLog(
                entity_type="agent_run",
                entity_id=agent_run.id,
                action=(
                    "completed_crm_trigger_aware_workflow"
                ),
                actor_type="agent",
                actor_name="origination-agent-v3",
                before_data=None,
                after_data={
                    "company_id": company.id,
                    "company_name": company.name,
                    "trigger_count": len(triggers),
                    "contact_count": len(contacts),
                    "interaction_count": len(interactions),
                    "priority_score_id": priority_score.id,
                    "overall_score": (
                        priority_score.overall_score
                    ),
                    "relationship_score": (
                        priority_score.relationship_score
                    ),
                    "email_draft_id": email_draft.id,
                    "recipient_name": (
                        email_draft.recipient_name
                    ),
                },
            )

            self.audit_log_repository.create(
                audit_log
            )

            persist_completed_at = datetime.now(timezone.utc)
            persist_step.status = "completed"
            persist_step.completed_at = persist_completed_at
            persist_step.duration_ms = max(
                0,
                int(
                    (persist_completed_at - persist_step.started_at).total_seconds()
                    * 1000
                ),
            )
            persist_step.output_summary = "Run, score, draft and audit persisted"

            self.db.commit()

            self.db.refresh(agent_run)
            self.db.refresh(priority_score)
            self.db.refresh(email_draft)

            return AgentRunDetail(
                agent_run=AgentRunRead.model_validate(
                    agent_run
                ),
                priority_score=(
                    PriorityScoreRead.model_validate(
                        priority_score
                    )
                ),
                email_draft=(
                    EmailDraftRead.model_validate(
                        email_draft
                    )
                ),
            )

        except Exception as error:
            self.db.rollback()

            if agent_run.id is not None:
                persisted_run = self.agent_run_repository.get_by_id(agent_run.id)
                if persisted_run is not None:
                    persisted_run.status = "failed"
                    persisted_run.error_message = "Workflow execution failed"
                    persisted_run.completed_at = datetime.now(timezone.utc)

                    failed_step_id = locals().get("persist_step_id") or locals().get(
                        "workflow_step_id"
                    )
                    failed_step = (
                        self.agent_run_step_repository.get_by_id(failed_step_id)
                        if isinstance(failed_step_id, int)
                        else None
                    )
                    if failed_step is not None:
                        failed_step.status = "failed"
                        failed_step.completed_at = datetime.now(timezone.utc)
                        failed_step.error_code = type(error).__name__
                        failed_step.error_message = "Workflow execution failed"
                    self.db.commit()

            raise
