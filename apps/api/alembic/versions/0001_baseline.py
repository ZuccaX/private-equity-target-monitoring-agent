"""Freeze the pre-Alembic application schema.

Revision ID: 0001_baseline
Revises: None
"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column[object], sa.Column[object]]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(500)),
        sa.Column("domain", sa.String(255), unique=True),
        sa.Column("sector", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("source", sa.String(100)),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("external_id", sa.String(255)),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False),
        *_timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_companies_name", "companies", ["name"])
    op.create_index("ix_companies_status", "companies", ["status"])
    op.create_index("ix_companies_domain", "companies", ["domain"])
    op.create_index("ix_companies_id", "companies", ["id"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("job_title", sa.String(255)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(100)),
        sa.Column("relationship_strength", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("external_id", sa.String(255), unique=True),
        *_timestamps(),
    )
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])
    op.create_index("ix_contacts_id", "contacts", ["id"])

    op.create_table(
        "crm_interactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id")),
        sa.Column("interaction_type", sa.String(100), nullable=False),
        sa.Column("direction", sa.String(50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("external_id", sa.String(255), unique=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_crm_interactions_company_id", "crm_interactions", ["company_id"])
    op.create_index("ix_crm_interactions_contact_id", "crm_interactions", ["contact_id"])
    op.create_index("ix_crm_interactions_interaction_type", "crm_interactions", ["interaction_type"])
    op.create_index("ix_crm_interactions_occurred_at", "crm_interactions", ["occurred_at"])
    op.create_index("ix_crm_interactions_id", "crm_interactions", ["id"])

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("url", sa.String(1000)),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_news_articles_company_id", "news_articles", ["company_id"])
    op.create_index("ix_news_articles_id", "news_articles", ["id"])

    op.create_table(
        "triggers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("news_article_id", sa.Integer(), sa.ForeignKey("news_articles.id")),
        sa.Column("trigger_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_triggers_company_id", "triggers", ["company_id"])
    op.create_index("ix_triggers_news_article_id", "triggers", ["news_article_id"])
    op.create_index("ix_triggers_trigger_type", "triggers", ["trigger_type"])
    op.create_index("ix_triggers_id", "triggers", ["id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("source_system", sa.String(100), nullable=False),
        sa.Column("source_path", sa.String(1000)),
        sa.Column("mime_type", sa.String(255)),
        sa.Column("content_text", sa.Text()),
        sa.Column("uploaded_at", sa.DateTime(timezone=True)),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("external_id", sa.String(255)),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False),
        *_timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_documents_company_id", "documents", ["company_id"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_source_system", "documents", ["source_system"])
    op.create_index(
        "ix_documents_external_id", "documents", ["external_id"], unique=True
    )
    op.create_index("ix_documents_id", "documents", ["id"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint(
            "document_id", "chunk_index", name="uq_document_chunks_document_id_chunk_index"
        ),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_company_id", "document_chunks", ["company_id"])
    op.create_index("ix_document_chunks_id", "document_chunks", ["id"])

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("run_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("workflow_version", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100)),
        sa.Column("prompt_version", sa.String(50)),
        sa.Column("input_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("output_summary", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_agent_runs_company_id", "agent_runs", ["company_id"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])
    op.create_index("ix_agent_runs_id", "agent_runs", ["id"])

    op.create_table(
        "priority_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("score_version", sa.String(50), nullable=False),
        sa.Column("sector_fit_score", sa.Integer(), nullable=False),
        sa.Column("trigger_score", sa.Integer(), nullable=False),
        sa.Column("relationship_score", sa.Integer(), nullable=False),
        sa.Column("timing_score", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("reasons", postgresql.JSONB(), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_priority_scores_overall_score_range",
        ),
    )
    op.create_index("ix_priority_scores_agent_run_id", "priority_scores", ["agent_run_id"])
    op.create_index("ix_priority_scores_company_id", "priority_scores", ["company_id"])
    op.create_index("ix_priority_scores_id", "priority_scores", ["id"])

    op.create_table(
        "email_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("tone", sa.String(50), nullable=False),
        sa.Column("recipient_name", sa.String(255)),
        sa.Column("recipient_email", sa.String(255)),
        sa.Column("generated_by", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100)),
        sa.Column("prompt_version", sa.String(50)),
        sa.Column("evidence_refs", postgresql.JSONB(), nullable=False),
        *_timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_email_drafts_agent_run_id", "email_drafts", ["agent_run_id"])
    op.create_index("ix_email_drafts_company_id", "email_drafts", ["company_id"])
    op.create_index("ix_email_drafts_status", "email_drafts", ["status"])
    op.create_index("ix_email_drafts_id", "email_drafts", ["id"])

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email_draft_id", sa.Integer(), sa.ForeignKey("email_drafts.id"), nullable=False),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("reviewer_name", sa.String(255)),
        sa.Column("reviewer_role", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_approvals_email_draft_id", "approvals", ["email_draft_id"])
    op.create_index("ix_approvals_decision", "approvals", ["decision"])
    op.create_index("ix_approvals_id", "approvals", ["id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Integer()),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("actor_type", sa.String(50), nullable=False),
        sa.Column("actor_name", sa.String(255)),
        sa.Column("before_data", postgresql.JSONB()),
        sa.Column("after_data", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])


def downgrade() -> None:
    for table_name in (
        "audit_logs",
        "approvals",
        "email_drafts",
        "priority_scores",
        "agent_runs",
        "document_chunks",
        "documents",
        "triggers",
        "news_articles",
        "crm_interactions",
        "contacts",
        "companies",
    ):
        op.drop_table(table_name)
    op.execute("DROP EXTENSION IF EXISTS vector")
