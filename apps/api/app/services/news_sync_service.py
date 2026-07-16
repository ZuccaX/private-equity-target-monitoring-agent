from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.news.base import NewsFetchError
from app.integrations.news.config import NewsSourceConfig, NewsSourceRegistry
from app.integrations.news.http_client import BoundedNewsHttpClient
from app.integrations.news.mock import MockNewsAdapter
from app.integrations.news.public_page import PublicPageNewsAdapter
from app.integrations.news.rss import RssNewsAdapter
from app.integrations.news.url_safety import URLSafetyPolicy
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.news_ingestion_service import (
    NewsIngestionError,
    NewsIngestionService,
)
from app.services.trigger_extraction_service import (
    build_trigger_extraction_service,
)


class SourceSyncError(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    category: str
    retryable: bool = False
    http_status: int | None = None


class NewsSyncReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok", "partial", "failed"]
    requested_sources: int = Field(ge=0)
    succeeded_sources: int = Field(ge=0)
    fetched: int = Field(ge=0)
    accepted: int = Field(ge=0)
    created: int = Field(ge=0)
    updated: int = Field(ge=0)
    duplicates: int = Field(ge=0)
    rejected: int = Field(ge=0)
    failed: int = Field(ge=0)
    triggers_created: int = Field(default=0, ge=0)
    triggers_merged: int = Field(default=0, ge=0)
    fallback_count: int = Field(default=0, ge=0)
    errors: tuple[SourceSyncError, ...] = ()

    @model_validator(mode="after")
    def validate_invariants(self) -> "NewsSyncReport":
        if self.accepted != self.created + self.updated + self.duplicates:
            raise ValueError("accepted article count invariant failed")
        if self.fetched != self.accepted + self.rejected + self.failed:
            raise ValueError("fetched article count invariant failed")
        if self.succeeded_sources > self.requested_sources:
            raise ValueError("source count invariant failed")
        return self


class NewsSyncOrchestrator:
    def __init__(
        self,
        db: Session,
        *,
        registry: NewsSourceRegistry,
        settings: Settings,
        audit_repository: AuditLogRepository | None = None,
    ) -> None:
        self.db = db
        self.registry = registry
        self.settings = settings
        self.audit_repository = audit_repository or AuditLogRepository(db)

    def sync(
        self,
        *,
        source_ids: list[str] | None = None,
        extract_triggers: bool = True,
        max_items_per_source: int | None = None,
    ) -> NewsSyncReport:
        sources = self.registry.resolve_enabled(source_ids)
        max_items = min(
            max_items_per_source or self.settings.news_max_items,
            self.settings.news_max_items,
        )
        totals = {
            "fetched": 0,
            "accepted": 0,
            "created": 0,
            "updated": 0,
            "duplicates": 0,
            "rejected": 0,
            "failed": 0,
            "triggers_created": 0,
            "triggers_merged": 0,
            "fallback_count": 0,
        }
        errors: list[SourceSyncError] = []
        succeeded = 0
        for source in sources:
            try:
                adapter = self._adapter(source)
                items = adapter.fetch(max_items=max_items)
            except NewsFetchError as exc:
                errors.append(
                    SourceSyncError(
                        source_id=source.source_id,
                        category=exc.category,
                        retryable=exc.retryable,
                        http_status=exc.http_status,
                    )
                )
                continue
            except (OSError, ValueError):
                errors.append(
                    SourceSyncError(
                        source_id=source.source_id,
                        category="source_fetch_failed",
                        retryable=False,
                    )
                )
                continue

            local = {key: 0 for key in totals}
            local["fetched"] = len(items)
            try:
                with self.db.begin():
                    ingestion = NewsIngestionService(self.db)
                    extraction = build_trigger_extraction_service(
                        db=self.db,
                        configured_settings=self.settings,
                    )
                    article_ids: list[int] = []
                    trigger_ids: list[int] = []
                    for item in items:
                        try:
                            with self.db.begin_nested():
                                outcome = ingestion.ingest(item, source)
                                item_created = 0
                                item_merged = 0
                                item_fallbacks = 0
                                item_trigger_ids: tuple[int, ...] = ()
                                if (
                                    extract_triggers
                                    and outcome.article.trigger_extraction_status
                                    == "pending"
                                ):
                                    trigger_outcome = extraction.extract_and_persist(
                                        outcome.article
                                    )
                                    item_created = trigger_outcome.created
                                    item_merged = trigger_outcome.merged
                                    item_fallbacks = len(trigger_outcome.fallbacks)
                                    item_trigger_ids = trigger_outcome.trigger_ids
                                    outcome.article.trigger_extraction_status = (
                                        "processed"
                                        if trigger_outcome.trigger_ids
                                        else "no_trigger"
                                    )
                                    outcome.article.trigger_extracted_at = datetime.now(
                                        timezone.utc
                                    )
                                    outcome.article.trigger_extraction_version = (
                                        self.settings.trigger_extraction_version
                                    )
                            action_key = (
                                "duplicates"
                                if outcome.action == "duplicate"
                                else outcome.action
                            )
                            local[action_key] += 1
                            local["accepted"] += 1
                            local["triggers_created"] += item_created
                            local["triggers_merged"] += item_merged
                            local["fallback_count"] += item_fallbacks
                            article_ids.append(outcome.article.id)
                            trigger_ids.extend(item_trigger_ids)
                        except NewsIngestionError:
                            local["rejected"] += 1
                        except Exception:
                            local["failed"] += 1
                    self.audit_repository.create(
                        AuditLog(
                            entity_type="news_source",
                            entity_id=None,
                            action="news_sync",
                            actor_type="system",
                            actor_name="m3_news_sync",
                            after_data={
                                "source_id": source.source_id,
                                "adapter": source.adapter,
                                "counts": local,
                                "article_ids": sorted(set(article_ids)),
                                "trigger_ids": sorted(set(trigger_ids)),
                            },
                        )
                    )
                for key in totals:
                    totals[key] += local[key]
                succeeded += 1
            except Exception:
                self.db.rollback()
                errors.append(
                    SourceSyncError(
                        source_id=source.source_id,
                        category="source_transaction_failed",
                        retryable=True,
                    )
                )

        if succeeded == len(sources):
            status = "ok"
        elif succeeded:
            status = "partial"
        else:
            status = "failed"
        return NewsSyncReport(
            status=status,
            requested_sources=len(sources),
            succeeded_sources=succeeded,
            errors=tuple(errors),
            **totals,
        )

    def _adapter(self, source: NewsSourceConfig):
        if source.adapter == "mock":
            return MockNewsAdapter(source, self.registry)
        if not source.allowed_host or (
            source.allowed_host.lower()
            not in self.settings.news_allowed_host_list
        ):
            raise NewsFetchError("host_not_globally_allowlisted")
        client = BoundedNewsHttpClient(
            policy=URLSafetyPolicy(allowed_hosts={source.allowed_host}),
            max_response_bytes=self.settings.news_max_response_bytes,
            max_redirects=self.settings.news_max_redirects,
            max_retries=self.settings.news_max_retries,
            min_host_interval_seconds=(
                self.settings.news_host_min_interval_seconds
            ),
            timeout_seconds=self.settings.news_http_timeout_seconds,
            connect_timeout_seconds=(
                self.settings.news_http_connect_timeout_seconds
            ),
        )
        if source.adapter == "rss":
            return RssNewsAdapter(source, client)
        return PublicPageNewsAdapter(source, client)
