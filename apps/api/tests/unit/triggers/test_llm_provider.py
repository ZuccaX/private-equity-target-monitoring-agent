import json
from datetime import datetime, timezone

import httpx

from app.models.news_article import NewsArticle
from app.services.trigger_providers.llm import LLMTriggerProvider


def _article() -> NewsArticle:
    return NewsArticle(
        id=1,
        company_id=1,
        title="Asteria update",
        summary="Asteria launched a new analytics platform.",
        published_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )


def _provider(handler) -> LLMTriggerProvider:
    return LLMTriggerProvider(
        endpoint="https://llm.example.com/v1/chat/completions",
        model="fixture-model",
        api_key="test-only-key",
        allowed_hosts={"llm.example.com"},
        resolver=lambda _host: ["93.184.216.34"],
        transport=httpx.MockTransport(handler),
    )


def test_llm_provider_validates_structured_candidate() -> None:
    payload = [
        {
            "trigger_type": "product_launch",
            "title": "Asteria update",
            "description": "A launch",
            "confidence_score": 0.91,
            "evidence_sentence": "Asteria launched a new analytics platform.",
            "event_date": "2026-07-10T00:00:00Z",
            "extraction_method": "llm",
        }
    ]
    provider = _provider(
        lambda _request: httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
        )
    )

    result = provider.extract(_article())

    assert len(result.candidates) == 1
    assert result.candidates[0].trigger_type == "product_launch"
    assert result.fallbacks == ()


def test_llm_provider_falls_back_on_invalid_evidence_or_response() -> None:
    invalid = _provider(
        lambda _request: httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                [
                                    {
                                        "trigger_type": "funding",
                                        "title": "Invented",
                                        "confidence_score": 0.9,
                                        "evidence_sentence": "Invented evidence.",
                                        "event_date": "2026-07-10T00:00:00Z",
                                        "extraction_method": "llm",
                                    }
                                ]
                            )
                        }
                    }
                ]
            },
        )
    )
    result = invalid.extract(_article())
    assert result.candidates == ()
    assert result.fallbacks == ("llm_invalid_output",)

    unavailable = _provider(lambda _request: httpx.Response(503))
    assert unavailable.extract(_article()).fallbacks == ("llm_unavailable",)
