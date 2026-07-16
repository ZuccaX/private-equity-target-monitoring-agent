import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.integrations.news.config import NewsSourceConfig, NewsSourceRegistry


def _source(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_id": "demo_mock",
        "adapter": "mock",
        "enabled": True,
        "fixture_path": "news_sync_items.json",
        "reliability": 0.8,
    }
    payload.update(overrides)
    return payload


def test_registry_loads_checked_in_mock_source() -> None:
    settings = Settings(_env_file=None)
    registry = NewsSourceRegistry.load(
        settings.news_source_config,
        fixture_root=settings.news_fixture_root,
    )

    assert registry.enabled_ids == ("demo_mock",)
    assert registry.resolve_enabled(["demo_mock"])[0].adapter == "mock"


def test_registry_rejects_duplicate_and_disabled_sources(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        NewsSourceRegistry(
            [NewsSourceConfig.model_validate(_source())] * 2,
            fixture_root=tmp_path,
        )

    registry = NewsSourceRegistry(
        [
            NewsSourceConfig.model_validate(
                _source(source_id="off", enabled=False)
            )
        ],
        fixture_root=tmp_path,
    )
    with pytest.raises(ValueError, match="not enabled"):
        registry.resolve_enabled(["off"])


@pytest.mark.parametrize("adapter", ["rss", "public_page"])
def test_network_source_requires_https_and_exact_host(adapter: str) -> None:
    with pytest.raises(ValidationError):
        NewsSourceConfig.model_validate(
            _source(
                adapter=adapter,
                fixture_path=None,
                url="http://news.example.com/feed",
                allowed_host="news.example.com",
                selectors={"item": "article"},
            )
        )

    with pytest.raises(ValidationError):
        NewsSourceConfig.model_validate(
            _source(
                adapter=adapter,
                fixture_path=None,
                url="https://news.example.com/feed",
                allowed_host="other.example.com",
                selectors={"item": "article"},
            )
        )


def test_public_page_requires_selectors() -> None:
    with pytest.raises(ValidationError, match="selectors"):
        NewsSourceConfig.model_validate(
            _source(
                adapter="public_page",
                fixture_path=None,
                url="https://news.example.com/",
                allowed_host="news.example.com",
            )
        )


def test_mock_fixture_cannot_escape_fixture_root(tmp_path: Path) -> None:
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        json.dumps([_source(fixture_path="../secret.json")]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="fixture root"):
        NewsSourceRegistry.load(config_path, fixture_root=tmp_path / "fixtures")
