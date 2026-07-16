from datetime import datetime, timezone

from app.services.trigger_extraction_service import (
    event_fingerprint,
    jaccard_similarity,
)


def test_event_fingerprint_is_deterministic_and_non_sensitive() -> None:
    date = datetime(2026, 7, 10, tzinfo=timezone.utc)
    first = event_fingerprint(
        1, "customer_win", date, "Asteria won a hospital contract"
    )
    second = event_fingerprint(
        1, "customer_win", date, "  asteria WON a hospital contract. "
    )
    assert first == second
    assert len(first) == 64
    assert "asteria" not in first


def test_jaccard_similarity_has_expected_boundaries() -> None:
    assert jaccard_similarity("same event", "same event") == 1
    assert jaccard_similarity("customer won", "cyber breach") == 0
