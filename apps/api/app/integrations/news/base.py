from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class RawNewsItem:
    source_item_id: str | None
    title: str
    url: str | None = None
    summary: str | None = None
    content: str | None = None
    published_at: datetime | str | None = None
    language: str | None = None
    company_domain: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class NewsFetchError(RuntimeError):
    def __init__(
        self,
        category: str,
        *,
        retryable: bool = False,
        http_status: int | None = None,
    ) -> None:
        super().__init__(category)
        self.category = category
        self.retryable = retryable
        self.http_status = http_status


class NewsAdapter(Protocol):
    def fetch(self, *, max_items: int) -> list[RawNewsItem]: ...
