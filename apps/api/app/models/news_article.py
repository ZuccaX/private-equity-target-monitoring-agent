from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class NewsArticle(TimestampMixin, Base):
    __tablename__ = "news_articles"

    __table_args__ = (
        CheckConstraint(
            "source_reliability >= 0 AND source_reliability <= 1",
            name="ck_news_articles_source_reliability",
        ),
        CheckConstraint(
            "company_match_confidence >= 0 AND company_match_confidence <= 1",
            name="ck_news_articles_company_match_confidence",
        ),
        UniqueConstraint(
            "company_id",
            "content_hash",
            name="uq_news_articles_company_content_hash",
        ),
        UniqueConstraint(
            "company_id",
            "canonical_url",
            name="uq_news_articles_company_canonical_url",
        ),
        CheckConstraint(
            "ingestion_status IN ('ingested', 'updated')",
            name="ck_news_articles_ingestion_status",
        ),
        CheckConstraint(
            "trigger_extraction_status IN "
            "('pending', 'processed', 'no_trigger', 'failed')",
            name="ck_news_articles_trigger_extraction_status",
        ),
        Index(
            "ix_news_articles_trigger_extraction",
            "trigger_extraction_status",
            "trigger_extraction_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        default="mock_news",
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    canonical_url: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, index=True
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    language: Mapped[str] = mapped_column(
        String(16), default="en", nullable=False
    )
    source_reliability: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )
    company_match_confidence: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    ingestion_status: Mapped[str] = mapped_column(
        String(50), default="ingested", nullable=False, index=True
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    trigger_extraction_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    trigger_extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trigger_extraction_version: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
