from datetime import timezone

from app.integrations.news.normalization import (
    content_hash,
    normalize_text,
    normalize_url,
    parse_datetime_utc,
    sanitize_html,
)


def test_normalize_url_removes_tracking_fragment_and_default_port() -> None:
    assert normalize_url(
        "https://NEWS.example.com:443/a//b?utm_source=x&id=7&drop=1#part",
        allowed_query_keys={"id"},
    ) == "https://news.example.com/a/b?id=7"


def test_sanitize_html_removes_executable_markup_and_bounds_text() -> None:
    value = sanitize_html(
        '<div onclick="x()">Safe <script>steal()</script><style>x</style> text</div>',
        max_length=20,
    )

    assert value == "Safe text"
    assert "steal" not in value


def test_time_text_and_hash_are_deterministic() -> None:
    parsed = parse_datetime_utc("2026-07-10T10:00:00+02:00")
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert parsed.isoformat() == "2026-07-10T08:00:00+00:00"
    assert normalize_text("  A\n  B  ", max_length=20) == "A B"
    assert content_hash(" A ", " B ") == content_hash("A", "B")
    assert len(content_hash("A", "B")) == 64
