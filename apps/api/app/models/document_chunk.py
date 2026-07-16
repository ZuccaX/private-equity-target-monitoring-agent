from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            "embedding_provider",
            "embedding_model",
            "embedding_model_version",
            "embedding_dimension",
            name="uq_chunks_document_index_model",
        ),
        Index(
            "ix_chunks_embedding_cohort",
            "embedding_provider",
            "embedding_model",
            "embedding_model_version",
            "embedding_dimension",
        ),
        Index(
            "ix_chunks_hash_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
            postgresql_where=text(
                "embedding_provider='hashing' AND "
                "embedding_model='local-hashing-384-v1' AND "
                "embedding_model_version='1' AND embedding_dimension=384"
            ),
        ),
        Index(
            "ix_chunks_minilm_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
            postgresql_where=text(
                "embedding_provider='sentence_transformer' AND "
                "embedding_model='sentence-transformers/all-MiniLM-L6-v2' "
                "AND embedding_model_version="
                "'1110a243fdf4706b3f48f1d95db1a4f5529b4d41' "
                "AND embedding_dimension=384"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(100),
        default="local-hashing-384-v1",
        nullable=False,
    )

    embedding_provider: Mapped[str] = mapped_column(
        String(50), default="hashing", nullable=False
    )
    embedding_model_version: Mapped[str] = mapped_column(
        String(64), default="1", nullable=False
    )
    embedding_dimension: Mapped[int] = mapped_column(
        Integer, default=384, nullable=False
    )
    source_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_file_version: Mapped[str] = mapped_column(String(100), nullable=False)

    extra_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
