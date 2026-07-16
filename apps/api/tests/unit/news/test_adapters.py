import json
from pathlib import Path

import pytest

from app.integrations.news.config import NewsSourceConfig, NewsSourceRegistry
from app.integrations.news.http_client import FetchedDocument
from app.integrations.news.mock import MockNewsAdapter
from app.integrations.news.public_page import PublicPageNewsAdapter
from app.integrations.news.rss import RssNewsAdapter


FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "news"


class FixtureClient:
    def __init__(self, fixture: str, content_type: str) -> None:
        self.fixture = fixture
        self.content_type = content_type

    def get(self, url: str) -> FetchedDocument:
        return FetchedDocument(
            url=url,
            status=200,
            content_type=self.content_type,
            body=(FIXTURE_ROOT / self.fixture).read_bytes(),
        )


@pytest.mark.parametrize(
    ("fixture", "expected_id"),
    [("rss.xml", "rss-1"), ("atom.xml", "atom-1")],
)
def test_rss_and_atom_are_parsed_without_network(
    fixture: str, expected_id: str
) -> None:
    source = NewsSourceConfig(
        source_id="feed",
        adapter="rss",
        url="https://news.example.com/feed",
        allowed_host="news.example.com",
    )
    items = RssNewsAdapter(
        source,
        FixtureClient(fixture, "application/xml"),
    ).fetch(max_items=1)

    assert len(items) == 1
    assert items[0].source_item_id == expected_id
    assert items[0].url == "https://news.example.com/article/1"


def test_rss_rejects_dtd_entity_payload(tmp_path: Path) -> None:
    malicious = tmp_path / "bad.xml"
    malicious.write_text(
        '<!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        "<rss><channel><item><title>&xxe;</title></item></channel></rss>",
        encoding="utf-8",
    )
    source = NewsSourceConfig(
        source_id="feed",
        adapter="rss",
        url="https://news.example.com/feed",
        allowed_host="news.example.com",
    )

    class MaliciousClient:
        def get(self, url: str) -> FetchedDocument:
            return FetchedDocument(
                url=url,
                status=200,
                content_type="application/xml",
                body=malicious.read_bytes(),
            )

    with pytest.raises(ValueError, match="XML"):
        RssNewsAdapter(source, MaliciousClient()).fetch(max_items=10)


def test_public_page_uses_configured_selectors_and_sanitizes() -> None:
    source = NewsSourceConfig(
        source_id="page",
        adapter="public_page",
        url="https://news.example.com/news",
        allowed_host="news.example.com",
        selectors={
            "item": "article",
            "title": "h2",
            "link": "a",
            "summary": ".summary",
            "published_at": "time",
        },
    )
    items = PublicPageNewsAdapter(
        source,
        FixtureClient("public_page.html", "text/html"),
    ).fetch(max_items=1)

    assert len(items) == 1
    assert items[0].title == "Asteria expands"
    assert items[0].url == "https://news.example.com/articles/asteria"
    assert "alert" not in (items[0].summary or "")


def test_mock_adapter_is_bounded_and_uses_safe_registry_path(
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    (fixture_root / "items.json").write_text(
        json.dumps(
            [
                {"source_item_id": "one", "title": "One"},
                {"source_item_id": "two", "title": "Two"},
            ]
        ),
        encoding="utf-8",
    )
    source = NewsSourceConfig(
        source_id="mock",
        adapter="mock",
        fixture_path="items.json",
    )
    registry = NewsSourceRegistry([source], fixture_root=fixture_root)

    assert len(MockNewsAdapter(source, registry).fetch(max_items=1)) == 1
