import pytest
from pydantic import ValidationError

from app.services.news_sync_service import NewsSyncReport, SourceSyncError


def test_report_enforces_article_counter_invariants_and_safe_errors() -> None:
    report = NewsSyncReport(
        status="partial",
        requested_sources=2,
        succeeded_sources=1,
        fetched=3,
        accepted=2,
        created=1,
        updated=0,
        duplicates=1,
        rejected=1,
        failed=0,
        triggers_created=1,
        triggers_merged=0,
        fallback_count=0,
        errors=(
            SourceSyncError(
                source_id="feed",
                category="timeout",
                retryable=True,
            ),
        ),
    )
    assert report.accepted == report.created + report.updated + report.duplicates
    assert report.fetched == report.accepted + report.rejected + report.failed
    assert "body" not in SourceSyncError.model_fields
    assert "url" not in SourceSyncError.model_fields

    with pytest.raises(ValidationError):
        NewsSyncReport(
            status="ok",
            requested_sources=1,
            succeeded_sources=1,
            fetched=1,
            accepted=0,
            created=1,
            updated=0,
            duplicates=0,
            rejected=0,
            failed=0,
        )
