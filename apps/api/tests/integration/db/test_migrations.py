from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect, text
import pytest

from app import models  # noqa: F401
from app.core.database import Base
from app.core.migrations import migrate_database
from app.core.schema_compatibility import (
    baseline_schema_issues,
    milestone_1_schema_issues,
    milestone_2_schema_issues,
    milestone_3_schema_issues,
)


BASELINE_TABLES = {
    "agent_runs",
    "approvals",
    "audit_logs",
    "companies",
    "contacts",
    "crm_interactions",
    "document_chunks",
    "documents",
    "email_drafts",
    "news_articles",
    "priority_scores",
    "triggers",
}

MILESTONE_1_TABLES = {
    "agent_run_steps",
    "email_revisions",
    "feedback",
    "investment_mandates",
}


def _insert_legacy_document_and_chunk(
    engine: Engine,
    *,
    content_hash: str | None = None,
    embedding_model: str = "local-hashing-384-v1",
) -> None:
    embedding = "[" + ",".join(["0"] * 384) + "]"
    with engine.begin() as connection:
        company_id = connection.execute(
            text(
                "INSERT INTO companies (name, sector, country, status, "
                "extra_data, created_at, updated_at, pipeline_stage, "
                "first_seen_at) VALUES ('Migration Co', 'Software', 'France', "
                "'active', '{}'::jsonb, NOW(), NOW(), 'sourced', NOW()) "
                "RETURNING id"
            )
        ).scalar_one()
        document_id = connection.execute(
            text(
                "INSERT INTO documents (company_id, title, file_name, "
                "document_type, source_system, content_text, ingested_at, "
                "extra_data, created_at, updated_at, sync_status, content_hash) "
                "VALUES (:company_id, 'Memo', 'memo.txt', 'memo', 'fixture', "
                "'canonical content', NOW(), '{}'::jsonb, NOW(), NOW(), "
                "'synced', :content_hash) RETURNING id"
            ),
            {"company_id": company_id, "content_hash": content_hash},
        ).scalar_one()
        connection.execute(
            text(
                "INSERT INTO document_chunks (document_id, company_id, "
                "chunk_index, chunk_text, token_count, embedding, "
                "embedding_model, extra_data, created_at, updated_at) "
                "VALUES (:document_id, :company_id, 0, 'canonical content', 2, "
                "CAST(:embedding AS vector), :embedding_model, '{}'::jsonb, "
                "NOW(), NOW())"
            ),
            {
                "document_id": document_id,
                "company_id": company_id,
                "embedding": embedding,
                "embedding_model": embedding_model,
            },
        )


def test_clean_upgrade_downgrade_and_reupgrade(
    alembic_config: Config,
    test_engine: Engine,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "0001_baseline")
    assert BASELINE_TABLES <= set(inspect(test_engine).get_table_names())
    assert baseline_schema_issues(test_engine) == []

    command.upgrade(alembic_config, "head")
    inspector = inspect(test_engine)
    assert MILESTONE_1_TABLES <= set(inspector.get_table_names())
    assert milestone_2_schema_issues(test_engine) == []
    assert {
        "mandate_id",
        "pipeline_stage",
        "owner",
        "first_seen_at",
        "next_action",
    } <= {column["name"] for column in inspector.get_columns("companies")}

    command.downgrade(alembic_config, "0001_baseline")
    assert MILESTONE_1_TABLES.isdisjoint(inspect(test_engine).get_table_names())
    assert baseline_schema_issues(test_engine) == []

    command.upgrade(alembic_config, "head")
    assert MILESTONE_1_TABLES <= set(inspect(test_engine).get_table_names())
    command.check(alembic_config)


def test_unversioned_baseline_can_be_stamped_and_preserves_data(
    alembic_config: Config,
    test_engine: Engine,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "0001_baseline")
    with test_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO companies (
                    name, sector, country, status, extra_data,
                    created_at, updated_at
                ) VALUES (
                    'Existing Company', 'Software', 'France', 'active',
                    '{}'::jsonb, NOW(), NOW()
                )
                """
            )
        )
        connection.execute(text("DROP TABLE alembic_version"))

    assert baseline_schema_issues(test_engine) == []
    outcome = migrate_database(test_engine, alembic_config)

    with test_engine.connect() as connection:
        company = connection.execute(
            text(
                """
                SELECT name, pipeline_stage, first_seen_at
                FROM companies
                WHERE name = 'Existing Company'
                """
            )
        ).one()

    assert company.name == "Existing Company"
    assert company.pipeline_stage == "sourced"
    assert company.first_seen_at is not None
    assert outcome == "upgraded_compatible_baseline_database"


def test_unversioned_milestone_1_schema_is_stamped_then_upgraded(
    alembic_config: Config,
    test_engine: Engine,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "0002_milestone1_core")
    with test_engine.begin() as connection:
        connection.execute(text("DROP TABLE alembic_version"))

    outcome = migrate_database(test_engine, alembic_config)

    with test_engine.connect() as connection:
        version = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    assert outcome == "upgraded_compatible_milestone_1_database"
    assert version == "0004_milestone3_news_triggers"
    assert milestone_2_schema_issues(test_engine) == []


def test_create_all_partial_schema_is_repaired_without_data_loss(
    alembic_config: Config,
    test_engine: Engine,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "0001_baseline")
    with test_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO companies (
                    name, sector, country, status, extra_data,
                    created_at, updated_at
                ) VALUES (
                    'Partial Schema Company', 'Software', 'France', 'active',
                    '{}'::jsonb, NOW(), NOW()
                )
                """
            )
        )
        connection.execute(text("DROP TABLE alembic_version"))

    for table_name in (
        "investment_mandates",
        "agent_run_steps",
        "feedback",
        "email_revisions",
    ):
        Base.metadata.tables[table_name].create(test_engine)

    outcome = migrate_database(test_engine, alembic_config)

    assert outcome == "repaired_create_all_partial_database"
    assert milestone_1_schema_issues(test_engine) == []
    with test_engine.connect() as connection:
        assert connection.execute(
            text("SELECT count(*) FROM companies WHERE name='Partial Schema Company'")
        ).scalar_one() == 1


def test_m2_upgrade_rejects_mismatched_document_content_hash(
    alembic_config: Config,
    test_engine: Engine,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "0002_milestone1_core")
    _insert_legacy_document_and_chunk(test_engine, content_hash="0" * 64)

    with pytest.raises(RuntimeError, match="content_hash"):
        command.upgrade(alembic_config, "head")


def test_m2_upgrade_rejects_unknown_legacy_embedding_model(
    alembic_config: Config,
    test_engine: Engine,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "0002_milestone1_core")
    _insert_legacy_document_and_chunk(test_engine, embedding_model="unknown")

    with pytest.raises(RuntimeError, match="Unknown legacy"):
        command.upgrade(alembic_config, "head")


def test_m2_multi_cohort_downgrade_is_refused_without_data_loss(
    alembic_config: Config,
    test_engine: Engine,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "0002_milestone1_core")
    _insert_legacy_document_and_chunk(test_engine)
    command.upgrade(alembic_config, "head")
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO document_chunks (document_id, company_id, "
                "chunk_index, chunk_text, token_count, embedding, "
                "embedding_provider, embedding_model, embedding_model_version, "
                "embedding_dimension, source_content_hash, source_file_version, "
                "extra_data, created_at, updated_at) SELECT document_id, "
                "company_id, chunk_index, chunk_text, token_count, embedding, "
                "'sentence_transformer', "
                "'sentence-transformers/all-MiniLM-L6-v2', "
                "'1110a243fdf4706b3f48f1d95db1a4f5529b4d41', 384, "
                "source_content_hash, source_file_version, extra_data, NOW(), "
                "NOW() FROM document_chunks WHERE embedding_provider='hashing'"
            )
        )

    with pytest.raises(RuntimeError, match="multiple embedding cohorts"):
        command.downgrade(alembic_config, "0002_milestone1_core")

    with test_engine.connect() as connection:
        assert connection.execute(
            text("SELECT count(*) FROM document_chunks")
        ).scalar_one() == 2


def test_m3_upgrade_backfills_trigger_identity_and_lifecycle(
    alembic_config: Config,
    test_engine: Engine,
    reset_test_schema: None,
) -> None:
    command.upgrade(alembic_config, "0003_milestone2_vector_cohorts")
    with test_engine.begin() as connection:
        company_id = connection.execute(
            text(
                "INSERT INTO companies (name, sector, country, status, "
                "extra_data, created_at, updated_at, pipeline_stage, "
                "first_seen_at) VALUES ('M3 Migration Co', 'Software', "
                "'France', 'active', '{}'::jsonb, NOW(), NOW(), 'sourced', "
                "NOW()) RETURNING id"
            )
        ).scalar_one()
        article_id = connection.execute(
            text(
                "INSERT INTO news_articles (company_id, title, source, "
                "ingested_at, raw_payload, created_at, updated_at, language, "
                "source_reliability, company_match_confidence, "
                "ingestion_status) VALUES (:company_id, 'Legacy article', "
                "'legacy', NOW(), '{}'::jsonb, NOW(), NOW(), 'en', 0.5, 1.0, "
                "'ingested') RETURNING id"
            ),
            {"company_id": company_id},
        ).scalar_one()
        trigger_id = connection.execute(
            text(
                "INSERT INTO triggers (company_id, news_article_id, "
                "trigger_type, title, confidence_score, detected_at, "
                "evidence_refs, extraction_method, is_negative, review_status, "
                "created_at, updated_at) VALUES (:company_id, :article_id, "
                "'growth', 'Legacy trigger', 0.8, NOW(), '[]'::jsonb, 'rules', "
                "false, 'unreviewed', NOW(), NOW()) RETURNING id"
            ),
            {"company_id": company_id, "article_id": article_id},
        ).scalar_one()

    command.upgrade(alembic_config, "head")

    assert milestone_3_schema_issues(test_engine) == []
    with test_engine.connect() as connection:
        lifecycle = connection.execute(
            text(
                "SELECT trigger_extraction_status, trigger_extracted_at, "
                "trigger_extraction_version FROM news_articles WHERE id=:id"
            ),
            {"id": article_id},
        ).one()
        dedupe_key = connection.execute(
            text("SELECT deduplication_key FROM triggers WHERE id=:id"),
            {"id": trigger_id},
        ).scalar_one()
    assert lifecycle.trigger_extraction_status == "pending"
    assert lifecycle.trigger_extracted_at is None
    assert lifecycle.trigger_extraction_version is None
    assert dedupe_key == f"legacy:{trigger_id}"

    command.downgrade(alembic_config, "0003_milestone2_vector_cohorts")
    assert "trigger_extraction_status" not in {
        column["name"]
        for column in inspect(test_engine).get_columns("news_articles")
    }
    command.upgrade(alembic_config, "head")
    command.check(alembic_config)
