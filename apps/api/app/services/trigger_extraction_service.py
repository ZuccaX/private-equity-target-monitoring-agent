import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.news_article import NewsArticle
from app.models.trigger import Trigger
from app.repositories.trigger_repository import TriggerRepository
from app.services.trigger_providers.base import (
    TriggerCandidate,
    TriggerProviderResult,
)
from app.services.trigger_providers.rules import RuleTriggerProvider
from app.services.trigger_providers.llm import LLMTriggerProvider


def _event_tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold()))


def jaccard_similarity(left: str, right: str) -> float:
    left_tokens = _event_tokens(left)
    right_tokens = _event_tokens(right)
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def event_fingerprint(
    company_id: int,
    trigger_type: str,
    event_date: datetime,
    evidence: str,
) -> str:
    tokens = " ".join(sorted(_event_tokens(evidence)))
    material = f"{company_id}|{trigger_type}|{event_date.date().isoformat()}|{tokens}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TriggerPersistenceResult:
    created: int
    merged: int
    trigger_ids: tuple[int, ...]
    fallbacks: tuple[str, ...]


class TriggerExtractionService:
    def __init__(
        self,
        *,
        rules: RuleTriggerProvider | None = None,
        mode: str = "rules",
        llm=None,
        db: Session | None = None,
        event_merge_days: int = 7,
        event_merge_similarity: float = 0.7,
    ) -> None:
        self.rules = rules or RuleTriggerProvider()
        if mode not in {"rules", "hybrid"}:
            raise ValueError("unsupported trigger extraction mode")
        self.mode = mode
        self.llm = llm
        self.db = db
        self.repository = TriggerRepository(db) if db is not None else None
        self.event_merge_days = event_merge_days
        self.event_merge_similarity = event_merge_similarity

    def extract_candidates(
        self,
        news_article: NewsArticle,
    ) -> TriggerProviderResult:
        rule_candidates = tuple(self.rules.extract(news_article))
        if self.mode != "hybrid" or self.llm is None or rule_candidates:
            return TriggerProviderResult(candidates=rule_candidates)
        supplemental = self.llm.extract(news_article)
        seen_types = {item.trigger_type for item in rule_candidates}
        merged = rule_candidates + tuple(
            item
            for item in supplemental.candidates
            if item.trigger_type not in seen_types
        )
        return TriggerProviderResult(
            candidates=merged,
            fallbacks=supplemental.fallbacks,
        )

    def extract_from_news_article(
        self,
        news_article: NewsArticle,
    ) -> list[TriggerCandidate]:
        return list(self.extract_candidates(news_article).candidates)

    def extract_and_persist(
        self,
        news_article: NewsArticle,
    ) -> TriggerPersistenceResult:
        if self.repository is None:
            raise RuntimeError("database session is required for persistence")
        result = self.extract_candidates(news_article)
        created = 0
        merged = 0
        trigger_ids: list[int] = []
        for candidate in result.candidates:
            trigger = self.repository.get_by_article_type(
                news_article.id, candidate.trigger_type
            )
            if trigger is None:
                for existing in self.repository.list_event_candidates(
                    company_id=news_article.company_id,
                    trigger_type=candidate.trigger_type,
                    event_date=candidate.event_date,
                    window_days=self.event_merge_days,
                ):
                    if jaccard_similarity(
                        existing.evidence_sentence or "",
                        candidate.evidence_sentence,
                    ) >= self.event_merge_similarity:
                        trigger = existing
                        break
            evidence_ref = {
                "type": "news_article",
                "news_article_id": news_article.id,
            }
            if trigger is not None:
                refs = list(trigger.evidence_refs or [])
                if evidence_ref not in refs:
                    refs.append(evidence_ref)
                trigger.evidence_refs = refs[:20]
                trigger.confidence_score = max(
                    trigger.confidence_score, candidate.confidence_score
                )
                if trigger.review_status not in {"confirmed", "rejected"}:
                    trigger.review_status = "unreviewed"
                self.db.flush()
                merged += 1
            else:
                trigger = Trigger(
                    company_id=news_article.company_id,
                    news_article_id=news_article.id,
                    trigger_type=candidate.trigger_type,
                    title=candidate.title,
                    description=candidate.description,
                    confidence_score=candidate.confidence_score,
                    event_date=candidate.event_date,
                    evidence_sentence=candidate.evidence_sentence,
                    extraction_method=candidate.extraction_method,
                    deduplication_key=event_fingerprint(
                        news_article.company_id,
                        candidate.trigger_type,
                        candidate.event_date,
                        candidate.evidence_sentence,
                    ),
                    is_negative=candidate.is_negative,
                    review_status="unreviewed",
                    evidence_refs=[evidence_ref],
                )
                self.repository.create(trigger)
                created += 1
            trigger_ids.append(trigger.id)
        return TriggerPersistenceResult(
            created=created,
            merged=merged,
            trigger_ids=tuple(trigger_ids),
            fallbacks=result.fallbacks,
        )


def build_trigger_extraction_service(
    *,
    configured_settings: Settings,
    db: Session | None = None,
) -> TriggerExtractionService:
    llm = None
    if configured_settings.trigger_extraction_mode == "hybrid":
        llm = LLMTriggerProvider(
            endpoint=configured_settings.trigger_llm_endpoint or "",
            model=configured_settings.trigger_llm_model or "",
            api_key=os.environ.get(
                configured_settings.trigger_llm_api_key_env, ""
            ),
            allowed_hosts=set(
                configured_settings.trigger_llm_allowed_host_list
            ),
            timeout_seconds=configured_settings.news_http_timeout_seconds,
        )
    return TriggerExtractionService(
        db=db,
        mode=configured_settings.trigger_extraction_mode,
        llm=llm,
        event_merge_days=configured_settings.news_event_merge_days,
        event_merge_similarity=(
            configured_settings.news_event_merge_similarity
        ),
    )
