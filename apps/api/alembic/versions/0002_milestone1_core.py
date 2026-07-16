"""Add infrastructure-era core models and compatibility fields.

Revision ID: 0002_milestone1_core
Revises: 0001_baseline
"""

from collections.abc import Sequence
from typing import Any

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_milestone1_core"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _create_table_if_missing(
    table_name: str, *columns: Any
) -> None:
    if not _table_exists(table_name):
        op.create_table(table_name, *columns)


def _create_index_if_missing(
    index_name: str,
    table_name: str,
    columns: list[str],
) -> None:
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    if index_name not in {index["name"] for index in indexes}:
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    _create_table_if_missing(
        "investment_mandates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("target_sectors", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("excluded_sectors", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("target_countries", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("revenue_min", sa.Float()),
        sa.Column("revenue_max", sa.Float()),
        sa.Column("ebitda_min", sa.Float()),
        sa.Column("ebitda_max", sa.Float()),
        sa.Column("growth_min", sa.Float()),
        sa.Column("growth_max", sa.Float()),
        sa.Column("ticket_size_min", sa.Float()),
        sa.Column("ticket_size_max", sa.Float()),
        sa.Column(
            "preferred_business_models",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "revenue_min IS NULL OR revenue_max IS NULL OR revenue_min <= revenue_max",
            name="ck_investment_mandates_revenue_range",
        ),
        sa.CheckConstraint(
            "ebitda_min IS NULL OR ebitda_max IS NULL OR ebitda_min <= ebitda_max",
            name="ck_investment_mandates_ebitda_range",
        ),
        sa.CheckConstraint(
            "growth_min IS NULL OR growth_max IS NULL OR growth_min <= growth_max",
            name="ck_investment_mandates_growth_range",
        ),
        sa.CheckConstraint(
            "ticket_size_min IS NULL OR ticket_size_max IS NULL OR "
            "ticket_size_min <= ticket_size_max",
            name="ck_investment_mandates_ticket_range",
        ),
    )
    _create_index_if_missing(
        "ix_investment_mandates_is_active",
        "investment_mandates",
        ["is_active"],
    )
    _create_index_if_missing(
        "ix_investment_mandates_id", "investment_mandates", ["id"]
    )

    op.add_column("companies", sa.Column("mandate_id", sa.Integer()))
    op.add_column(
        "companies",
        sa.Column("pipeline_stage", sa.String(50), nullable=False, server_default="sourced"),
    )
    op.add_column("companies", sa.Column("owner", sa.String(255)))
    op.add_column("companies", sa.Column("source_channel", sa.String(100)))
    op.add_column("companies", sa.Column("first_seen_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE companies SET first_seen_at = created_at WHERE first_seen_at IS NULL")
    op.alter_column(
        "companies",
        "first_seen_at",
        nullable=False,
        server_default=sa.func.now(),
    )
    op.add_column("companies", sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.add_column("companies", sa.Column("contacted_at", sa.DateTime(timezone=True)))
    op.add_column("companies", sa.Column("next_action", sa.String(100)))
    op.add_column("companies", sa.Column("next_action_due_at", sa.DateTime(timezone=True)))
    op.add_column("companies", sa.Column("pass_reason", sa.Text()))
    op.create_foreign_key(
        "fk_companies_mandate_id",
        "companies",
        "investment_mandates",
        ["mandate_id"],
        ["id"],
    )
    op.create_check_constraint(
        "ck_companies_pipeline_stage",
        "companies",
        "pipeline_stage IN ('sourced', 'monitoring', 'triggered', 'screening', "
        "'qualified', 'contacted', 'in_conversation', 'passed', 'archived')",
    )
    op.create_index("ix_companies_mandate_id", "companies", ["mandate_id"])
    op.create_index("ix_companies_pipeline_stage", "companies", ["pipeline_stage"])
    op.create_index("ix_companies_next_action_due_at", "companies", ["next_action_due_at"])

    _create_table_if_missing(
        "agent_run_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "agent_run_id",
            sa.Integer(),
            sa.ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("node_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("input_summary", sa.Text()),
        sa.Column("output_summary", sa.Text()),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fallback_reason", sa.Text()),
        sa.Column("error_code", sa.String(100)),
        sa.Column("error_message", sa.Text()),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'skipped')",
            name="ck_agent_run_steps_status",
        ),
    )
    _create_index_if_missing(
        "ix_agent_run_steps_agent_run_id", "agent_run_steps", ["agent_run_id"]
    )
    _create_index_if_missing(
        "ix_agent_run_steps_node_name", "agent_run_steps", ["node_name"]
    )
    _create_index_if_missing(
        "ix_agent_run_steps_status", "agent_run_steps", ["status"]
    )
    _create_index_if_missing("ix_agent_run_steps_id", "agent_run_steps", ["id"])

    _create_table_if_missing(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_run_id", sa.Integer(), sa.ForeignKey("agent_runs.id", ondelete="CASCADE")),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE")),
        sa.Column("feedback_type", sa.String(50), nullable=False),
        sa.Column("rating", sa.Integer()),
        sa.Column("is_helpful", sa.Boolean()),
        sa.Column("comment", sa.Text()),
        sa.Column("submitted_by", sa.String(255)),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "feedback_type IN ('rag_relevance', 'trigger_accuracy', 'score_quality', "
            "'recommended_action', 'email_quality', 'overall_run')",
            name="ck_feedback_type",
        ),
        sa.CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="ck_feedback_rating",
        ),
    )
    _create_index_if_missing(
        "ix_feedback_agent_run_id", "feedback", ["agent_run_id"]
    )
    _create_index_if_missing("ix_feedback_company_id", "feedback", ["company_id"])
    _create_index_if_missing(
        "ix_feedback_feedback_type", "feedback", ["feedback_type"]
    )
    _create_index_if_missing("ix_feedback_id", "feedback", ["id"])

    _create_table_if_missing(
        "email_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "email_draft_id",
            sa.Integer(),
            sa.ForeignKey("email_drafts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("editor_name", sa.String(255)),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    _create_index_if_missing(
        "ix_email_revisions_email_draft_id",
        "email_revisions",
        ["email_draft_id"],
    )
    _create_index_if_missing("ix_email_revisions_id", "email_revisions", ["id"])

    op.add_column("news_articles", sa.Column("canonical_url", sa.String(1000)))
    op.add_column("news_articles", sa.Column("content_hash", sa.String(64)))
    op.add_column(
        "news_articles",
        sa.Column("language", sa.String(16), nullable=False, server_default="en"),
    )
    op.add_column(
        "news_articles",
        sa.Column("source_reliability", sa.Float(), nullable=False, server_default="0.5"),
    )
    op.add_column(
        "news_articles",
        sa.Column(
            "company_match_confidence", sa.Float(), nullable=False, server_default="1.0"
        ),
    )
    op.add_column(
        "news_articles",
        sa.Column("ingestion_status", sa.String(50), nullable=False, server_default="ingested"),
    )
    op.add_column("news_articles", sa.Column("external_id", sa.String(255)))
    op.create_check_constraint(
        "ck_news_articles_source_reliability",
        "news_articles",
        "source_reliability >= 0 AND source_reliability <= 1",
    )
    op.create_check_constraint(
        "ck_news_articles_company_match_confidence",
        "news_articles",
        "company_match_confidence >= 0 AND company_match_confidence <= 1",
    )
    op.create_unique_constraint(
        "uq_news_articles_company_content_hash",
        "news_articles",
        ["company_id", "content_hash"],
    )
    op.create_unique_constraint(
        "uq_news_articles_external_id",
        "news_articles",
        ["external_id"],
    )
    op.create_index("ix_news_articles_canonical_url", "news_articles", ["canonical_url"])
    op.create_index("ix_news_articles_content_hash", "news_articles", ["content_hash"])
    op.create_index("ix_news_articles_ingestion_status", "news_articles", ["ingestion_status"])

    op.add_column("triggers", sa.Column("event_date", sa.DateTime(timezone=True)))
    op.add_column("triggers", sa.Column("evidence_sentence", sa.Text()))
    op.add_column(
        "triggers",
        sa.Column("extraction_method", sa.String(50), nullable=False, server_default="rules"),
    )
    op.add_column("triggers", sa.Column("deduplication_key", sa.String(255)))
    op.add_column(
        "triggers",
        sa.Column("is_negative", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "triggers",
        sa.Column("review_status", sa.String(50), nullable=False, server_default="unreviewed"),
    )
    op.create_unique_constraint(
        "uq_triggers_company_deduplication_key",
        "triggers",
        ["company_id", "deduplication_key"],
    )
    op.create_index("ix_triggers_event_date", "triggers", ["event_date"])
    op.create_index("ix_triggers_is_negative", "triggers", ["is_negative"])
    op.create_index("ix_triggers_review_status", "triggers", ["review_status"])

    op.add_column("documents", sa.Column("content_hash", sa.String(64)))
    op.add_column("documents", sa.Column("file_version", sa.String(100)))
    op.add_column(
        "documents",
        sa.Column("sync_status", sa.String(50), nullable=False, server_default="synced"),
    )
    op.add_column("documents", sa.Column("last_synced_at", sa.DateTime(timezone=True)))
    op.add_column("documents", sa.Column("indexed_at", sa.DateTime(timezone=True)))
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])
    op.create_index("ix_documents_sync_status", "documents", ["sync_status"])


def downgrade() -> None:
    op.drop_index("ix_documents_sync_status", table_name="documents")
    op.drop_index("ix_documents_content_hash", table_name="documents")
    for column_name in (
        "indexed_at",
        "last_synced_at",
        "sync_status",
        "file_version",
        "content_hash",
    ):
        op.drop_column("documents", column_name)

    op.drop_index("ix_triggers_review_status", table_name="triggers")
    op.drop_index("ix_triggers_is_negative", table_name="triggers")
    op.drop_index("ix_triggers_event_date", table_name="triggers")
    op.drop_constraint(
        "uq_triggers_company_deduplication_key", "triggers", type_="unique"
    )
    for column_name in (
        "review_status",
        "is_negative",
        "deduplication_key",
        "extraction_method",
        "evidence_sentence",
        "event_date",
    ):
        op.drop_column("triggers", column_name)

    op.drop_index("ix_news_articles_ingestion_status", table_name="news_articles")
    op.drop_index("ix_news_articles_content_hash", table_name="news_articles")
    op.drop_index("ix_news_articles_canonical_url", table_name="news_articles")
    op.drop_constraint("uq_news_articles_external_id", "news_articles", type_="unique")
    op.drop_constraint(
        "uq_news_articles_company_content_hash", "news_articles", type_="unique"
    )
    op.drop_constraint(
        "ck_news_articles_company_match_confidence", "news_articles", type_="check"
    )
    op.drop_constraint(
        "ck_news_articles_source_reliability", "news_articles", type_="check"
    )
    for column_name in (
        "external_id",
        "ingestion_status",
        "company_match_confidence",
        "source_reliability",
        "language",
        "content_hash",
        "canonical_url",
    ):
        op.drop_column("news_articles", column_name)

    op.drop_table("email_revisions")
    op.drop_table("feedback")
    op.drop_table("agent_run_steps")

    op.drop_index("ix_companies_next_action_due_at", table_name="companies")
    op.drop_index("ix_companies_pipeline_stage", table_name="companies")
    op.drop_index("ix_companies_mandate_id", table_name="companies")
    op.drop_constraint("ck_companies_pipeline_stage", "companies", type_="check")
    op.drop_constraint("fk_companies_mandate_id", "companies", type_="foreignkey")
    for column_name in (
        "pass_reason",
        "next_action_due_at",
        "next_action",
        "contacted_at",
        "reviewed_at",
        "first_seen_at",
        "source_channel",
        "owner",
        "pipeline_stage",
        "mandate_id",
    ):
        op.drop_column("companies", column_name)

    op.drop_table("investment_mandates")
