from datetime import datetime, timezone

from app.core.config import Settings
from app.models.news_article import NewsArticle
from app.services.trigger_extraction_service import (
    TriggerExtractionService,
    build_trigger_extraction_service,
)
from app.services.trigger_providers.base import (
    TriggerCandidate,
    TriggerProviderResult,
)


class SpyLLM:
    def __init__(self, result: TriggerProviderResult) -> None:
        self.result = result
        self.calls = 0

    def extract(self, article: NewsArticle) -> TriggerProviderResult:
        self.calls += 1
        return self.result


def _article(summary: str) -> NewsArticle:
    return NewsArticle(
        id=1,
        company_id=1,
        title="Asteria update",
        summary=summary,
        published_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )


def test_rules_mode_never_calls_llm() -> None:
    llm = SpyLLM(TriggerProviderResult())
    result = TriggerExtractionService(mode="rules", llm=llm).extract_candidates(
        _article("Asteria published a routine update.")
    )
    assert result.candidates == ()
    assert llm.calls == 0


def test_hybrid_supplements_uncovered_content_and_preserves_fallback() -> None:
    candidate = TriggerCandidate(
        trigger_type="funding",
        title="Asteria update",
        confidence_score=0.9,
        evidence_sentence="Asteria completed a financing transaction.",
        event_date=datetime(2026, 7, 10, tzinfo=timezone.utc),
        extraction_method="llm",
    )
    llm = SpyLLM(TriggerProviderResult(candidates=(candidate,)))
    result = TriggerExtractionService(mode="hybrid", llm=llm).extract_candidates(
        _article("Asteria completed a financing transaction.")
    )
    assert {item.trigger_type for item in result.candidates} == {"funding"}
    assert llm.calls == 1

    failing = SpyLLM(TriggerProviderResult(fallbacks=("llm_timeout",)))
    fallback = TriggerExtractionService(
        mode="hybrid", llm=failing
    ).extract_candidates(_article("Routine update."))
    assert fallback.fallbacks == ("llm_timeout",)


def test_configured_factory_wires_hybrid_provider_and_merge_controls() -> None:
    configured = Settings(
        _env_file=None,
        trigger_extraction_mode="hybrid",
        trigger_llm_endpoint=None,
        trigger_llm_model=None,
        news_event_merge_days=11,
        news_event_merge_similarity=0.82,
    )

    service = build_trigger_extraction_service(
        configured_settings=configured,
    )
    result = service.extract_candidates(_article("Routine update."))

    assert service.mode == "hybrid"
    assert service.llm is not None
    assert service.event_merge_days == 11
    assert service.event_merge_similarity == 0.82
    assert result.fallbacks == ("llm_not_configured",)
