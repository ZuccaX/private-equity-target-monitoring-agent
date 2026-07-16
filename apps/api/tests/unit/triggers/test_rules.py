from datetime import datetime, timezone

import pytest

from app.models.news_article import NewsArticle
from app.services.trigger_providers.rules import RuleTriggerProvider


@pytest.mark.parametrize(
    ("sentence", "expected_type", "negative"),
    [
        ("Asteria opened a new office in Lyon.", "market_expansion", False),
        ("Asteria launched a new platform.", "product_launch", False),
        ("Asteria formed a partnership with Delta.", "partnership", False),
        ("Asteria won a major hospital customer.", "customer_win", False),
        ("Asteria raised a Series B round.", "funding", False),
        ("Asteria appointed a new CFO.", "leadership_hire", False),
        ("Asteria acquired a French software vendor.", "acquisition", False),
        ("Asteria announced layoffs affecting 50 staff.", "layoffs", True),
        ("Asteria issued a profit warning.", "profit_warning", True),
        ("Asteria lost its largest customer.", "customer_loss", True),
        ("A regulator opened an investigation into Asteria.", "regulatory_issue", True),
        ("Asteria's CEO stepped down.", "management_departure", True),
        ("Asteria disclosed a cyber breach.", "cyber_incident", True),
        ("Asteria was sued in a contract lawsuit.", "litigation", True),
    ],
)
def test_rules_cover_all_canonical_categories(
    sentence: str,
    expected_type: str,
    negative: bool,
) -> None:
    article = NewsArticle(
        id=1,
        company_id=1,
        title="Company update",
        summary=sentence,
        published_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )

    candidates = RuleTriggerProvider().extract(article)

    assert any(item.trigger_type == expected_type for item in candidates)
    selected = next(
        item for item in candidates if item.trigger_type == expected_type
    )
    assert selected.is_negative is negative
    assert selected.evidence_sentence == sentence


def test_rules_return_multiple_types_and_explicit_event_date() -> None:
    article = NewsArticle(
        id=1,
        company_id=1,
        title="Two updates",
        summary=(
            "Asteria launched a platform on 2026-07-09. "
            "Asteria also appointed a new CFO."
        ),
        published_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )

    candidates = RuleTriggerProvider().extract(article)

    assert {item.trigger_type for item in candidates} == {
        "product_launch",
        "leadership_hire",
    }
    product = next(
        item for item in candidates if item.trigger_type == "product_launch"
    )
    assert product.event_date.date().isoformat() == "2026-07-09"


def test_rules_do_not_match_substrings_or_routine_update() -> None:
    article = NewsArticle(
        id=1,
        company_id=1,
        title="Routine update",
        summary="The relaunchpad handbook was updated.",
    )
    assert RuleTriggerProvider().extract(article) == []
