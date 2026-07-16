import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NewsSourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,63}$")
    adapter: Literal["mock", "rss", "public_page"]
    enabled: bool = True
    url: str | None = None
    allowed_host: str | None = None
    fixture_path: str | None = None
    company_domain: str | None = None
    company_aliases: tuple[str, ...] = ()
    reliability: float = Field(default=0.5, ge=0, le=1)
    language: str = Field(default="und", min_length=2, max_length=16)
    selectors: dict[str, str] = Field(default_factory=dict)
    allowed_query_keys: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_adapter_fields(self) -> "NewsSourceConfig":
        if self.adapter == "mock":
            if not self.fixture_path:
                raise ValueError("mock source requires fixture_path")
            if self.url or self.allowed_host:
                raise ValueError("mock source cannot configure network fields")
            return self

        if not self.url or not self.allowed_host:
            raise ValueError("network source requires URL and allowed_host")
        parsed = urlsplit(self.url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.hostname.lower() != self.allowed_host.lower()
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            raise ValueError("network source requires matching HTTPS host")
        if self.fixture_path:
            raise ValueError("network source cannot configure fixture_path")
        if self.adapter == "public_page":
            required = {"item", "title", "link"}
            if not required.issubset(self.selectors):
                raise ValueError("public_page requires item/title/link selectors")
        return self


class NewsSourceRegistry:
    def __init__(
        self,
        sources: list[NewsSourceConfig],
        *,
        fixture_root: Path,
    ) -> None:
        self.fixture_root = fixture_root.resolve()
        self._sources: dict[str, NewsSourceConfig] = {}
        for source in sources:
            if source.source_id in self._sources:
                raise ValueError(f"duplicate source_id: {source.source_id}")
            if source.fixture_path:
                self.fixture_path(source)
            self._sources[source.source_id] = source

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        fixture_root: Path,
    ) -> "NewsSourceRegistry":
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_sources = data["sources"] if isinstance(data, dict) else data
        if not isinstance(raw_sources, list):
            raise ValueError("news source configuration must be a list")
        sources = [NewsSourceConfig.model_validate(item) for item in raw_sources]
        return cls(sources, fixture_root=fixture_root)

    @property
    def enabled_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                source_id
                for source_id, source in self._sources.items()
                if source.enabled
            )
        )

    def resolve_enabled(
        self, source_ids: list[str] | tuple[str, ...] | None = None
    ) -> list[NewsSourceConfig]:
        selected = list(source_ids or self.enabled_ids)
        if len(selected) != len(set(selected)):
            raise ValueError("source IDs must be unique")
        resolved: list[NewsSourceConfig] = []
        for source_id in selected:
            source = self._sources.get(source_id)
            if source is None or not source.enabled:
                raise ValueError(f"source is unknown or not enabled: {source_id}")
            resolved.append(source)
        return resolved

    def fixture_path(self, source: NewsSourceConfig) -> Path:
        if not source.fixture_path:
            raise ValueError("source has no fixture")
        candidate = (self.fixture_root / source.fixture_path).resolve()
        try:
            candidate.relative_to(self.fixture_root)
        except ValueError as exc:
            raise ValueError("fixture path escapes fixture root") from exc
        return candidate
