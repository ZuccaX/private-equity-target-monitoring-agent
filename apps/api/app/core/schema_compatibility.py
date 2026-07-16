from collections.abc import Mapping

from sqlalchemy import Engine, inspect


BASELINE_SCHEMA: Mapping[str, frozenset[str]] = {
    "agent_runs": frozenset({"id", "company_id", "run_type", "status"}),
    "approvals": frozenset({"id", "email_draft_id", "decision"}),
    "audit_logs": frozenset({"id", "entity_type", "action", "actor_type"}),
    "companies": frozenset({"id", "name", "sector", "country", "status"}),
    "contacts": frozenset({"id", "company_id", "full_name"}),
    "crm_interactions": frozenset(
        {"id", "company_id", "interaction_type", "occurred_at"}
    ),
    "document_chunks": frozenset(
        {"id", "document_id", "company_id", "chunk_index", "embedding"}
    ),
    "documents": frozenset(
        {"id", "company_id", "title", "file_name", "document_type"}
    ),
    "email_drafts": frozenset({"id", "agent_run_id", "company_id", "status"}),
    "news_articles": frozenset({"id", "company_id", "title", "source"}),
    "priority_scores": frozenset(
        {"id", "agent_run_id", "company_id", "overall_score"}
    ),
    "triggers": frozenset({"id", "company_id", "trigger_type", "title"}),
}

MILESTONE_1_SCHEMA: Mapping[str, frozenset[str]] = {
    "agent_run_steps": frozenset(
        {"id", "agent_run_id", "node_name", "status", "fallback_used"}
    ),
    "companies": frozenset(
        {
            "mandate_id",
            "pipeline_stage",
            "owner",
            "first_seen_at",
            "next_action",
        }
    ),
    "documents": frozenset(
        {"content_hash", "file_version", "sync_status", "last_synced_at"}
    ),
    "email_revisions": frozenset({"id", "email_draft_id", "subject", "body"}),
    "feedback": frozenset({"id", "feedback_type", "rating", "is_helpful"}),
    "investment_mandates": frozenset(
        {"id", "name", "target_sectors", "target_countries", "is_active"}
    ),
    "news_articles": frozenset(
        {"canonical_url", "content_hash", "language", "ingestion_status"}
    ),
    "triggers": frozenset(
        {"event_date", "evidence_sentence", "deduplication_key", "is_negative"}
    ),
}

MILESTONE_2_SCHEMA: Mapping[str, frozenset[str]] = {
    "document_chunks": frozenset(
        {
            "embedding_provider",
            "embedding_model_version",
            "embedding_dimension",
            "source_content_hash",
            "source_file_version",
        }
    )
}

MILESTONE_3_SCHEMA: Mapping[str, frozenset[str]] = {
    "news_articles": frozenset(
        {
            "trigger_extraction_status",
            "trigger_extracted_at",
            "trigger_extraction_version",
        }
    ),
    "triggers": frozenset({"deduplication_key"}),
}


def baseline_schema_issues(engine: Engine) -> list[str]:
    """Return compatibility failures for a pre-Alembic repository database."""
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    issues: list[str] = []

    for table_name, required_columns in BASELINE_SCHEMA.items():
        if table_name not in actual_tables:
            issues.append(f"missing table: {table_name}")
            continue

        actual_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        for column_name in sorted(required_columns - actual_columns):
            issues.append(f"missing column: {table_name}.{column_name}")

    return issues


def milestone_1_schema_issues(engine: Engine) -> list[str]:
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    issues: list[str] = []

    for table_name, required_columns in MILESTONE_1_SCHEMA.items():
        if table_name not in actual_tables:
            issues.append(f"missing table: {table_name}")
            continue
        actual_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        for column_name in sorted(required_columns - actual_columns):
            issues.append(f"missing column: {table_name}.{column_name}")

    return issues


def milestone_2_schema_issues(engine: Engine) -> list[str]:
    inspector = inspect(engine)
    issues: list[str] = []
    for table_name, required_columns in MILESTONE_2_SCHEMA.items():
        if table_name not in inspector.get_table_names():
            issues.append(f"missing table: {table_name}")
            continue
        actual_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        for column_name in sorted(required_columns - actual_columns):
            issues.append(f"missing column: {table_name}.{column_name}")
    return issues


def milestone_3_schema_issues(engine: Engine) -> list[str]:
    inspector = inspect(engine)
    issues: list[str] = []
    for table_name, required_columns in MILESTONE_3_SCHEMA.items():
        if table_name not in inspector.get_table_names():
            issues.append(f"missing table: {table_name}")
            continue
        actual_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        for column_name in sorted(required_columns - actual_columns):
            issues.append(f"missing column: {table_name}.{column_name}")
    return issues
