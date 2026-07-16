import json

from app.integrations.news.base import RawNewsItem
from app.integrations.news.config import NewsSourceConfig, NewsSourceRegistry


class MockNewsAdapter:
    def __init__(
        self,
        source: NewsSourceConfig,
        registry: NewsSourceRegistry,
    ) -> None:
        self.source = source
        self.registry = registry

    def fetch(self, *, max_items: int) -> list[RawNewsItem]:
        path = self.registry.fixture_path(self.source)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("mock news fixture must contain a list")
        return [RawNewsItem(**item) for item in payload[:max_items]]
