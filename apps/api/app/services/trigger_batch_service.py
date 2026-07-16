from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.news_article_repository import NewsArticleRepository
from app.services.trigger_extraction_service import (
    TriggerExtractionService,
    build_trigger_extraction_service,
)


@dataclass(frozen=True, slots=True)
class TriggerBatchError:
    article_id: int
    category: str
    retryable: bool = False


@dataclass(frozen=True, slots=True)
class TriggerBatchReport:
    status: str
    requested: int
    selected: int
    succeeded: int
    failed: int
    no_trigger: int
    triggers_created: int
    triggers_merged: int
    fallback_count: int
    errors: tuple[TriggerBatchError, ...] = ()


class TriggerBatchService:
    def __init__(
        self,
        db: Session,
        *,
        extraction_service: TriggerExtractionService | None = None,
        audit_repository: AuditLogRepository | None = None,
        configured_settings: Settings | None = None,
        version: str = "m3-rules-v1",
    ) -> None:
        self.db = db
        self.news_repository = NewsArticleRepository(db)
        self.extraction_service = extraction_service or build_trigger_extraction_service(
            db=db,
            configured_settings=configured_settings or settings,
        )
        self.audit_repository = audit_repository or AuditLogRepository(db)
        self.version = version

    def process(
        self,
        *,
        article_ids: list[int] | None = None,
        company_id: int | None = None,
        status: str = "pending",
        limit: int = 100,
    ) -> TriggerBatchReport:
        selected_rows = self.news_repository.list_for_extraction(
            version=self.version,
            article_ids=article_ids,
            company_id=company_id,
            status=status,
            limit=limit,
        )
        selected_ids = [row.id for row in selected_rows]
        self.db.rollback()
        created = merged = succeeded = failed = no_trigger = fallbacks = 0
        errors: list[TriggerBatchError] = []
        for article_id in selected_ids:
            try:
                with self.db.begin():
                    article = self.news_repository.get_by_id(article_id)
                    if article is None:
                        raise RuntimeError("article_not_found")
                    outcome = self.extraction_service.extract_and_persist(article)
                    article.trigger_extraction_status = (
                        "processed" if outcome.trigger_ids else "no_trigger"
                    )
                    article.trigger_extracted_at = datetime.now(timezone.utc)
                    article.trigger_extraction_version = self.version
                    self.audit_repository.create(
                        AuditLog(
                            entity_type="news_article",
                            entity_id=article.id,
                            action="trigger_extraction",
                            actor_type="system",
                            actor_name="m3_trigger_batch",
                            after_data={
                                "version": self.version,
                                "status": article.trigger_extraction_status,
                                "trigger_ids": list(outcome.trigger_ids),
                                "created": outcome.created,
                                "merged": outcome.merged,
                                "fallbacks": list(outcome.fallbacks),
                            },
                        )
                    )
                    created += outcome.created
                    merged += outcome.merged
                    fallbacks += len(outcome.fallbacks)
                    no_trigger += int(not outcome.trigger_ids)
                succeeded += 1
            except Exception:
                self.db.rollback()
                failed += 1
                errors.append(
                    TriggerBatchError(article_id, "article_processing_failed", True)
                )
        if not selected_ids:
            aggregate_status = "ok"
        elif succeeded == len(selected_ids):
            aggregate_status = "ok"
        elif succeeded:
            aggregate_status = "partial"
        else:
            aggregate_status = "failed"
        return TriggerBatchReport(
            status=aggregate_status,
            requested=len(article_ids or []),
            selected=len(selected_ids),
            succeeded=succeeded,
            failed=failed,
            no_trigger=no_trigger,
            triggers_created=created,
            triggers_merged=merged,
            fallback_count=fallbacks,
            errors=tuple(errors),
        )
