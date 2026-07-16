"""Add M3 news extraction lifecycle and trigger integrity.

Revision ID: 0004_milestone3_news_triggers
Revises: 0003_milestone2_vector_cohorts
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_milestone3_news_triggers"
down_revision: str | None = "0003_milestone2_vector_cohorts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _reject_incompatible_data() -> None:
    connection = op.get_bind()
    checks = (
        (
            "SELECT id FROM news_articles WHERE ingestion_status NOT IN "
            "('ingested', 'updated') LIMIT 1",
            "unsupported news ingestion_status",
        ),
        (
            "SELECT id FROM triggers WHERE confidence_score < 0 OR "
            "confidence_score > 1 LIMIT 1",
            "trigger confidence_score outside 0..1",
        ),
        (
            "SELECT id FROM triggers WHERE extraction_method NOT IN "
            "('rules', 'llm', 'hybrid', 'seed') LIMIT 1",
            "unsupported trigger extraction_method",
        ),
        (
            "SELECT id FROM triggers WHERE review_status NOT IN "
            "('unreviewed', 'confirmed', 'rejected') LIMIT 1",
            "unsupported trigger review_status",
        ),
        (
            "SELECT min(id) FROM news_articles WHERE canonical_url IS NOT NULL "
            "GROUP BY company_id, canonical_url HAVING count(*) > 1 LIMIT 1",
            "duplicate company/canonical URL identity",
        ),
        (
            "SELECT min(id) FROM triggers WHERE news_article_id IS NOT NULL "
            "GROUP BY news_article_id, trigger_type HAVING count(*) > 1 LIMIT 1",
            "duplicate article/trigger type identity",
        ),
    )
    for statement, message in checks:
        if connection.execute(sa.text(statement)).scalar_one_or_none() is not None:
            raise RuntimeError(f"M3 migration refused: {message}.")


def upgrade() -> None:
    _reject_incompatible_data()
    op.add_column(
        "news_articles",
        sa.Column(
            "trigger_extraction_status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "news_articles",
        sa.Column("trigger_extracted_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "news_articles",
        sa.Column("trigger_extraction_version", sa.String(100)),
    )
    op.create_check_constraint(
        "ck_news_articles_ingestion_status",
        "news_articles",
        "ingestion_status IN ('ingested', 'updated')",
    )
    op.create_check_constraint(
        "ck_news_articles_trigger_extraction_status",
        "news_articles",
        "trigger_extraction_status IN "
        "('pending', 'processed', 'no_trigger', 'failed')",
    )
    op.create_unique_constraint(
        "uq_news_articles_company_canonical_url",
        "news_articles",
        ["company_id", "canonical_url"],
    )
    op.create_index(
        "ix_news_articles_trigger_extraction",
        "news_articles",
        ["trigger_extraction_status", "trigger_extraction_version"],
    )

    op.execute(
        "UPDATE triggers SET deduplication_key='legacy:' || id::text "
        "WHERE deduplication_key IS NULL"
    )
    op.alter_column("triggers", "deduplication_key", nullable=False)
    op.create_check_constraint(
        "ck_triggers_confidence_score",
        "triggers",
        "confidence_score >= 0 AND confidence_score <= 1",
    )
    op.create_check_constraint(
        "ck_triggers_extraction_method",
        "triggers",
        "extraction_method IN ('rules', 'llm', 'hybrid', 'seed')",
    )
    op.create_check_constraint(
        "ck_triggers_review_status",
        "triggers",
        "review_status IN ('unreviewed', 'confirmed', 'rejected')",
    )
    op.create_unique_constraint(
        "uq_triggers_news_article_type",
        "triggers",
        ["news_article_id", "trigger_type"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_triggers_news_article_type", "triggers", type_="unique"
    )
    op.drop_constraint(
        "ck_triggers_review_status", "triggers", type_="check"
    )
    op.drop_constraint(
        "ck_triggers_extraction_method", "triggers", type_="check"
    )
    op.drop_constraint(
        "ck_triggers_confidence_score", "triggers", type_="check"
    )
    op.alter_column("triggers", "deduplication_key", nullable=True)

    op.drop_index(
        "ix_news_articles_trigger_extraction", table_name="news_articles"
    )
    op.drop_constraint(
        "uq_news_articles_company_canonical_url",
        "news_articles",
        type_="unique",
    )
    op.drop_constraint(
        "ck_news_articles_trigger_extraction_status",
        "news_articles",
        type_="check",
    )
    op.drop_constraint(
        "ck_news_articles_ingestion_status", "news_articles", type_="check"
    )
    op.drop_column("news_articles", "trigger_extraction_version")
    op.drop_column("news_articles", "trigger_extracted_at")
    op.drop_column("news_articles", "trigger_extraction_status")
