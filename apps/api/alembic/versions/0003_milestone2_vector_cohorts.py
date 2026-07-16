"""Add isolated embedding cohorts and source identities.

Revision ID: 0003_milestone2_vector_cohorts
Revises: 0002_milestone1_core
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.core.content_identity import LEGACY_FILE_VERSION, canonical_content_hash


revision: str = "0003_milestone2_vector_cohorts"
down_revision: str | None = "0002_milestone1_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

HASH_PROVIDER = "hashing"
HASH_MODEL = "local-hashing-384-v1"
HASH_VERSION = "1"
SEMANTIC_PROVIDER = "sentence_transformer"
SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SEMANTIC_VERSION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def _backfill_and_validate_source_identity() -> None:
    connection = op.get_bind()
    documents = connection.execute(
        sa.text("SELECT id, content_text, content_hash, file_version FROM documents")
    ).mappings()
    for document in documents:
        expected = canonical_content_hash(document["content_text"])
        if document["content_hash"] not in (None, expected):
            raise RuntimeError(
                f"Document {document['id']} content_hash does not match canonical content."
            )
        connection.execute(
            sa.text(
                "UPDATE documents SET content_hash=:content_hash, "
                "file_version=COALESCE(file_version, :file_version) WHERE id=:id"
            ),
            {
                "content_hash": expected,
                "file_version": LEGACY_FILE_VERSION,
                "id": document["id"],
            },
        )

    unknown = connection.execute(
        sa.text(
            "SELECT DISTINCT embedding_model FROM document_chunks "
            "WHERE embedding_model <> :known"
        ),
        {"known": HASH_MODEL},
    ).scalars().all()
    if unknown:
        raise RuntimeError(f"Unknown legacy embedding model(s): {unknown}")


def _create_hnsw_indexes_when_supported() -> None:
    connection = op.get_bind()
    vector_version = connection.execute(
        sa.text("SELECT extversion FROM pg_extension WHERE extname='vector'")
    ).scalar_one_or_none()
    if vector_version is None:
        return
    parts = tuple(int(part) for part in vector_version.split(".")[:2])
    if parts < (0, 5):
        return
    op.execute(
        "CREATE INDEX ix_chunks_hash_hnsw ON document_chunks USING hnsw "
        "(embedding vector_cosine_ops) WHERE embedding_provider='hashing' "
        "AND embedding_model='local-hashing-384-v1' "
        "AND embedding_model_version='1' AND embedding_dimension=384"
    )
    op.execute(
        "CREATE INDEX ix_chunks_minilm_hnsw ON document_chunks USING hnsw "
        "(embedding vector_cosine_ops) WHERE "
        "embedding_provider='sentence_transformer' "
        "AND embedding_model='sentence-transformers/all-MiniLM-L6-v2' "
        "AND embedding_model_version='1110a243fdf4706b3f48f1d95db1a4f5529b4d41' "
        "AND embedding_dimension=384"
    )


def upgrade() -> None:
    _backfill_and_validate_source_identity()
    op.add_column(
        "document_chunks",
        sa.Column("embedding_provider", sa.String(50), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("embedding_model_version", sa.String(64), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("embedding_dimension", sa.Integer(), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("source_content_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("source_file_version", sa.String(100), nullable=True),
    )
    op.execute(
        "UPDATE document_chunks AS c SET embedding_provider='hashing', "
        "embedding_model_version='1', embedding_dimension=384, "
        "source_content_hash=d.content_hash, source_file_version=d.file_version "
        "FROM documents AS d WHERE d.id=c.document_id"
    )
    for column in (
        "embedding_provider",
        "embedding_model_version",
        "embedding_dimension",
        "source_content_hash",
        "source_file_version",
    ):
        op.alter_column("document_chunks", column, nullable=False)

    op.drop_constraint(
        "uq_document_chunks_document_id_chunk_index",
        "document_chunks",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_chunks_document_index_model",
        "document_chunks",
        [
            "document_id",
            "chunk_index",
            "embedding_provider",
            "embedding_model",
            "embedding_model_version",
            "embedding_dimension",
        ],
    )
    op.create_index(
        "ix_chunks_embedding_cohort",
        "document_chunks",
        [
            "embedding_provider",
            "embedding_model",
            "embedding_model_version",
            "embedding_dimension",
        ],
    )
    _create_hnsw_indexes_when_supported()


def downgrade() -> None:
    connection = op.get_bind()
    cohort_count = connection.execute(
        sa.text(
            "SELECT count(*) FROM (SELECT DISTINCT embedding_provider, "
            "embedding_model, embedding_model_version, embedding_dimension "
            "FROM document_chunks) AS cohorts"
        )
    ).scalar_one()
    if cohort_count > 1:
        raise RuntimeError(
            "Refusing to downgrade multiple embedding cohorts; export/prune first."
        )
    for index_name in ("ix_chunks_minilm_hnsw", "ix_chunks_hash_hnsw"):
        op.execute(f"DROP INDEX IF EXISTS {index_name}")
    op.drop_index("ix_chunks_embedding_cohort", table_name="document_chunks")
    op.drop_constraint(
        "uq_chunks_document_index_model", "document_chunks", type_="unique"
    )
    op.create_unique_constraint(
        "uq_document_chunks_document_id_chunk_index",
        "document_chunks",
        ["document_id", "chunk_index"],
    )
    for column in (
        "source_file_version",
        "source_content_hash",
        "embedding_dimension",
        "embedding_model_version",
        "embedding_provider",
    ):
        op.drop_column("document_chunks", column)
