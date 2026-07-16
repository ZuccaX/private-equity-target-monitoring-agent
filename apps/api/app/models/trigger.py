from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Float,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Trigger(TimestampMixin, Base):
    __tablename__ = "triggers"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "deduplication_key",
            name="uq_triggers_company_deduplication_key",
        ),
        UniqueConstraint(
            "news_article_id",
            "trigger_type",
            name="uq_triggers_news_article_type",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_triggers_confidence_score",
        ),
        CheckConstraint(
            "extraction_method IN ('rules', 'llm', 'hybrid', 'seed')",
            name="ck_triggers_extraction_method",
        ),
        CheckConstraint(
            "review_status IN ('unreviewed', 'confirmed', 'rejected')",
            name="ck_triggers_review_status",
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

    news_article_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_articles.id"),
        nullable=True,
        index=True,
    )

    trigger_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence_score: Mapped[float] = mapped_column(
        Float,
        default=0.8,
        nullable=False,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    evidence_refs: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    event_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    evidence_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_method: Mapped[str] = mapped_column(
        String(50), default="rules", nullable=False
    )
    deduplication_key: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    is_negative: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    review_status: Mapped[str] = mapped_column(
        String(50), default="unreviewed", nullable=False, index=True
    )
