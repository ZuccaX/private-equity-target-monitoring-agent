from dataclasses import dataclass
from typing import Any

from app.models.company import Company
from app.models.contact import Contact
from app.models.crm_interaction import CRMInteraction
from app.models.trigger import Trigger
from app.services.scoring_service import ScoreBreakdown


@dataclass
class EmailDraftContent:
    subject: str
    body: str
    tone: str
    recipient_name: str | None
    recipient_email: str | None
    generated_by: str
    model_name: str | None
    prompt_version: str | None
    evidence_refs: list[dict[str, Any]]


class EmailGenerationService:
    def generate_outreach_draft(
        self,
        company: Company,
        score: ScoreBreakdown,
        triggers: list[Trigger] | None = None,
        contacts: list[Contact] | None = None,
        interactions: list[CRMInteraction] | None = None,
    ) -> EmailDraftContent:
        normalized_triggers = triggers or []
        normalized_contacts = contacts or []
        normalized_interactions = interactions or []

        primary_contact = self._select_primary_contact(
            normalized_contacts
        )

        subject = self._build_subject(
            company=company,
            triggers=normalized_triggers,
        )

        body = self._build_body(
            company=company,
            triggers=normalized_triggers,
            primary_contact=primary_contact,
            interactions=normalized_interactions,
        )

        evidence_refs = self._build_evidence_refs(
            company=company,
            score=score,
            triggers=normalized_triggers,
            primary_contact=primary_contact,
            interactions=normalized_interactions,
        )

        return EmailDraftContent(
            subject=subject,
            body=body,
            tone="professional",
            recipient_name=(
                primary_contact.full_name
                if primary_contact is not None
                else f"{company.name} Team"
            ),
            recipient_email=(
                primary_contact.email
                if primary_contact is not None
                else None
            ),
            generated_by="template-crm-trigger-aware",
            model_name="template-only",
            prompt_version="v3-crm-trigger-aware",
            evidence_refs=evidence_refs,
        )

    def _select_primary_contact(
        self,
        contacts: list[Contact],
    ) -> Contact | None:
        if len(contacts) == 0:
            return None

        return max(
            contacts,
            key=lambda contact: contact.relationship_strength,
        )

    def _build_subject(
        self,
        company: Company,
        triggers: list[Trigger],
    ) -> str:
        if len(triggers) == 0:
            return (
                f"Following {company.name}'s "
                "recent momentum"
            )

        top_trigger = triggers[0]
        trigger_type = top_trigger.trigger_type

        if trigger_type == "market_expansion":
            return (
                f"Following {company.name}'s "
                "market expansion"
            )

        if trigger_type == "partnership":
            return (
                f"Following {company.name}'s "
                "recent partnership"
            )

        if trigger_type == "product_launch":
            return (
                f"Following {company.name}'s "
                "new product launch"
            )

        if trigger_type == "leadership_change":
            return (
                "Following recent leadership news at "
                f"{company.name}"
            )

        if trigger_type == "customer_win":
            return (
                f"Following {company.name}'s "
                "recent customer momentum"
            )

        return (
            f"Following {company.name}'s "
            "recent momentum"
        )

    def _build_body(
        self,
        company: Company,
        triggers: list[Trigger],
        primary_contact: Contact | None,
        interactions: list[CRMInteraction],
    ) -> str:
        greeting = self._build_greeting(
            company=company,
            primary_contact=primary_contact,
        )

        trigger_sentence = self._build_trigger_sentence(
            company=company,
            triggers=triggers,
        )

        relationship_sentence = (
            self._build_relationship_sentence(
                interactions
            )
        )

        body_parts = [
            greeting,
            "",
            trigger_sentence,
        ]

        if relationship_sentence is not None:
            body_parts.extend(
                [
                    "",
                    relationship_sentence,
                ]
            )

        body_parts.extend(
            [
                "",
                (
                    f"Given {company.name}'s position in "
                    f"{company.sector}, I thought it could "
                    "be worth continuing the conversation."
                ),
                "",
                "Best,",
                "Investment Team",
            ]
        )

        return "\n".join(body_parts)

    def _build_greeting(
        self,
        company: Company,
        primary_contact: Contact | None,
    ) -> str:
        if primary_contact is None:
            return f"Hi {company.name} team,"

        first_name = (
            primary_contact.full_name
            .strip()
            .split(" ")[0]
        )

        return f"Hi {first_name},"

    def _build_trigger_sentence(
        self,
        company: Company,
        triggers: list[Trigger],
    ) -> str:
        if len(triggers) == 0:
            return (
                f"I have been following {company.name}'s "
                f"work in {company.sector}."
            )

        top_trigger = triggers[0]

        return (
            "I noticed the recent development: "
            f"{top_trigger.title}."
        )

    def _build_relationship_sentence(
        self,
        interactions: list[CRMInteraction],
    ) -> str | None:
        if len(interactions) == 0:
            return None

        latest_interaction = max(
            interactions,
            key=lambda interaction: interaction.occurred_at,
        )

        interaction_label = (
            latest_interaction.interaction_type
            .replace("_", " ")
        )

        return (
            f"It was useful connecting during our recent "
            f"{interaction_label}, and I wanted to follow up."
        )

    def _build_evidence_refs(
        self,
        company: Company,
        score: ScoreBreakdown,
        triggers: list[Trigger],
        primary_contact: Contact | None,
        interactions: list[CRMInteraction],
    ) -> list[dict[str, Any]]:
        evidence_refs: list[dict[str, Any]] = [
            {
                "type": "priority_score",
                "overall_score": score.overall_score,
                "relationship_score": (
                    score.relationship_score
                ),
                "score_version": score.score_version,
            },
            {
                "type": "company_profile",
                "company_id": company.id,
                "company_name": company.name,
            },
        ]

        if primary_contact is not None:
            evidence_refs.append(
                {
                    "type": "crm_contact",
                    "contact_id": primary_contact.id,
                    "full_name": primary_contact.full_name,
                    "job_title": primary_contact.job_title,
                    "relationship_strength": (
                        primary_contact.relationship_strength
                    ),
                }
            )

        if len(interactions) > 0:
            latest_interaction = max(
                interactions,
                key=lambda interaction: interaction.occurred_at,
            )

            evidence_refs.append(
                {
                    "type": "crm_interaction",
                    "interaction_id": latest_interaction.id,
                    "interaction_type": (
                        latest_interaction.interaction_type
                    ),
                    "occurred_at": (
                        latest_interaction.occurred_at.isoformat()
                    ),
                    "sentiment_score": (
                        latest_interaction.sentiment_score
                    ),
                }
            )

        for trigger in triggers:
            evidence_refs.append(
                {
                    "type": "trigger",
                    "trigger_id": trigger.id,
                    "trigger_type": trigger.trigger_type,
                    "title": trigger.title,
                    "news_article_id": trigger.news_article_id,
                }
            )

        return evidence_refs