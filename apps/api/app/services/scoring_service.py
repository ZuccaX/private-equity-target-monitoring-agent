from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.models.company import Company
from app.models.contact import Contact
from app.models.crm_interaction import CRMInteraction
from app.models.trigger import Trigger


@dataclass
class ScoreBreakdown:
    overall_score: int
    score_version: str
    sector_fit_score: int
    trigger_score: int
    relationship_score: int
    timing_score: int
    risk_score: int
    reasons: list[str]
    evidence_refs: list[dict[str, Any]]


class ScoringService:
    def score_company(
        self,
        company: Company,
        triggers: list[Trigger] | None = None,
        contacts: list[Contact] | None = None,
        interactions: list[CRMInteraction] | None = None,
    ) -> ScoreBreakdown:
        normalized_triggers = triggers or []
        normalized_contacts = contacts or []
        normalized_interactions = interactions or []

        sector_fit_score = self._score_sector_fit(company.sector)

        trigger_score = self._score_triggers(
            normalized_triggers
        )

        relationship_score = self._score_relationship(
            contacts=normalized_contacts,
            interactions=normalized_interactions,
        )

        timing_score = self._score_timing(
            normalized_triggers
        )

        risk_score = self._score_risk(company)

        raw_score = (
            sector_fit_score
            + trigger_score
            + relationship_score
            + timing_score
            - risk_score
        )

        overall_score = min(
            100,
            max(0, raw_score),
        )

        reasons = self._build_reasons(
            company=company,
            triggers=normalized_triggers,
            contacts=normalized_contacts,
            interactions=normalized_interactions,
        )

        evidence_refs = self._build_evidence_refs(
            company=company,
            triggers=normalized_triggers,
            contacts=normalized_contacts,
            interactions=normalized_interactions,
        )

        return ScoreBreakdown(
            overall_score=overall_score,
            score_version="v3-crm-trigger-aware",
            sector_fit_score=sector_fit_score,
            trigger_score=trigger_score,
            relationship_score=relationship_score,
            timing_score=timing_score,
            risk_score=risk_score,
            reasons=reasons,
            evidence_refs=evidence_refs,
        )

    def _score_sector_fit(
        self,
        sector: str,
    ) -> int:
        sector_lower = sector.lower()

        preferred_keywords = [
            "data",
            "cyber",
            "saas",
            "fintech",
            "infrastructure",
        ]

        has_preferred_keyword = any(
            keyword in sector_lower
            for keyword in preferred_keywords
        )

        if has_preferred_keyword:
            return 25

        return 15

    def _score_triggers(
        self,
        triggers: list[Trigger],
    ) -> int:
        if len(triggers) == 0:
            return 5

        trigger_weights = {
            "market_expansion": 28,
            "partnership": 25,
            "product_launch": 23,
            "customer_win": 22,
            "leadership_change": 18,
            "funding": 16,
        }

        best_score = 10

        for trigger in triggers:
            type_score = trigger_weights.get(
                trigger.trigger_type,
                10,
            )

            confidence_bonus = int(
                trigger.confidence_score * 5
            )

            candidate_score = (
                type_score
                + confidence_bonus
            )

            best_score = max(
                best_score,
                candidate_score,
            )

        return min(best_score, 30)

    def _score_relationship(
        self,
        contacts: list[Contact],
        interactions: list[CRMInteraction],
    ) -> int:
        if len(contacts) == 0 and len(interactions) == 0:
            return 5

        strongest_relationship = max(
            (
                contact.relationship_strength
                for contact in contacts
            ),
            default=0,
        )

        contact_component = round(
            strongest_relationship
            / 100
            * 12
        )

        interaction_count_component = min(
            len(interactions),
            5,
        )

        recency_component = self._score_interaction_recency(
            interactions
        )

        sentiment_component = self._score_interaction_sentiment(
            interactions
        )

        relationship_score = (
            3
            + contact_component
            + interaction_count_component
            + recency_component
            + sentiment_component
        )

        return min(
            relationship_score,
            25,
        )

    def _score_interaction_recency(
        self,
        interactions: list[CRMInteraction],
    ) -> int:
        if len(interactions) == 0:
            return 0

        latest_interaction = max(
            interactions,
            key=lambda interaction: interaction.occurred_at,
        )

        occurred_at = latest_interaction.occurred_at

        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        days_since_interaction = max(
            0,
            (now - occurred_at).days,
        )

        if days_since_interaction <= 30:
            return 3

        if days_since_interaction <= 90:
            return 2

        if days_since_interaction <= 180:
            return 1

        return 0

    def _score_interaction_sentiment(
        self,
        interactions: list[CRMInteraction],
    ) -> int:
        if len(interactions) == 0:
            return 0

        average_sentiment = sum(
            interaction.sentiment_score
            for interaction in interactions
        ) / len(interactions)

        if average_sentiment >= 0.6:
            return 2

        if average_sentiment >= 0.2:
            return 1

        return 0

    def _score_timing(
        self,
        triggers: list[Trigger],
    ) -> int:
        if len(triggers) == 0:
            return 8

        high_timing_trigger_types = {
            "market_expansion",
            "partnership",
            "product_launch",
            "customer_win",
        }

        has_high_timing_trigger = any(
            trigger.trigger_type
            in high_timing_trigger_types
            for trigger in triggers
        )

        if has_high_timing_trigger:
            return 18

        return 12

    def _score_risk(
        self,
        company: Company,
    ) -> int:
        return 0

    def _build_reasons(
        self,
        company: Company,
        triggers: list[Trigger],
        contacts: list[Contact],
        interactions: list[CRMInteraction],
    ) -> list[str]:
        reasons = [
            (
                f"{company.name} operates in "
                f"{company.sector}, which matches "
                "the current investment theme."
            )
        ]

        if len(triggers) == 0:
            reasons.append(
                "No recent business trigger has been detected."
            )
        else:
            top_trigger = triggers[0]

            trigger_label = (
                top_trigger.trigger_type
                .replace("_", " ")
            )

            reasons.append(
                (
                    f"Recent {trigger_label} trigger detected: "
                    f"{top_trigger.title}."
                )
            )

        if len(contacts) == 0:
            reasons.append(
                "No CRM contact relationship is currently available."
            )
        else:
            strongest_contact = max(
                contacts,
                key=lambda contact: contact.relationship_strength,
            )

            reasons.append(
                (
                    f"CRM relationship with "
                    f"{strongest_contact.full_name} "
                    f"has strength "
                    f"{strongest_contact.relationship_strength}/100."
                )
            )

        if len(interactions) == 0:
            reasons.append(
                "No historical CRM interaction is currently recorded."
            )
        else:
            latest_interaction = max(
                interactions,
                key=lambda interaction: interaction.occurred_at,
            )

            reasons.append(
                (
                    f"Latest CRM interaction was a "
                    f"{latest_interaction.interaction_type} "
                    f"with sentiment score "
                    f"{latest_interaction.sentiment_score:.2f}."
                )
            )

        reasons.append(
            "No major negative risk signal is present "
            "in the current demo dataset."
        )

        return reasons

    def _build_evidence_refs(
        self,
        company: Company,
        triggers: list[Trigger],
        contacts: list[Contact],
        interactions: list[CRMInteraction],
    ) -> list[dict[str, Any]]:
        evidence_refs: list[dict[str, Any]] = [
            {
                "type": "company_profile",
                "company_id": company.id,
                "company_name": company.name,
                "sector": company.sector,
                "country": company.country,
            }
        ]

        for trigger in triggers:
            evidence_refs.append(
                {
                    "type": "trigger",
                    "trigger_id": trigger.id,
                    "trigger_type": trigger.trigger_type,
                    "title": trigger.title,
                    "confidence_score": trigger.confidence_score,
                    "news_article_id": trigger.news_article_id,
                }
            )

        for contact in contacts[:3]:
            evidence_refs.append(
                {
                    "type": "crm_contact",
                    "contact_id": contact.id,
                    "full_name": contact.full_name,
                    "job_title": contact.job_title,
                    "relationship_strength": (
                        contact.relationship_strength
                    ),
                }
            )

        for interaction in interactions[:3]:
            evidence_refs.append(
                {
                    "type": "crm_interaction",
                    "interaction_id": interaction.id,
                    "interaction_type": (
                        interaction.interaction_type
                    ),
                    "sentiment_score": (
                        interaction.sentiment_score
                    ),
                    "occurred_at": (
                        interaction.occurred_at.isoformat()
                    ),
                }
            )

        return evidence_refs