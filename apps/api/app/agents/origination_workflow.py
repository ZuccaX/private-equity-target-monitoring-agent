from dataclasses import dataclass

from app.models.company import Company
from app.models.contact import Contact
from app.models.crm_interaction import CRMInteraction
from app.models.trigger import Trigger
from app.services.email_generation_service import (
    EmailDraftContent,
    EmailGenerationService,
)
from app.services.scoring_service import (
    ScoreBreakdown,
    ScoringService,
)


@dataclass
class OriginationWorkflowResult:
    score: ScoreBreakdown
    email_draft: EmailDraftContent
    output_summary: str


class OriginationWorkflow:
    def __init__(
        self,
        scoring_service: ScoringService | None = None,
        email_generation_service: EmailGenerationService | None = None,
    ) -> None:
        self.scoring_service = (
            scoring_service
            or ScoringService()
        )

        self.email_generation_service = (
            email_generation_service
            or EmailGenerationService()
        )

    def run(
        self,
        company: Company,
        triggers: list[Trigger] | None = None,
        contacts: list[Contact] | None = None,
        interactions: list[CRMInteraction] | None = None,
    ) -> OriginationWorkflowResult:
        normalized_triggers = triggers or []
        normalized_contacts = contacts or []
        normalized_interactions = interactions or []

        score = self.scoring_service.score_company(
            company=company,
            triggers=normalized_triggers,
            contacts=normalized_contacts,
            interactions=normalized_interactions,
        )

        email_draft = (
            self.email_generation_service
            .generate_outreach_draft(
                company=company,
                score=score,
                triggers=normalized_triggers,
                contacts=normalized_contacts,
                interactions=normalized_interactions,
            )
        )

        output_summary = (
            f"Generated CRM and trigger-aware priority score "
            f"{score.overall_score} and email draft for "
            f"{company.name} using "
            f"{len(normalized_triggers)} trigger(s), "
            f"{len(normalized_contacts)} contact(s), and "
            f"{len(normalized_interactions)} interaction(s)."
        )

        return OriginationWorkflowResult(
            score=score,
            email_draft=email_draft,
            output_summary=output_summary,
        )