from datetime import datetime, timezone
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Company(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "companies"

    __table_args__ = (
        Index("ix_companies_domain", "domain"),
        CheckConstraint(
            "pipeline_stage IN ('sourced', 'monitoring', 'triggered', "
            "'screening', 'qualified', 'contacted', 'in_conversation', "
            "'passed', 'archived')",
            name="ck_companies_pipeline_stage",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    sector: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="new",
        nullable=False,
        index=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    extra_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    mandate_id: Mapped[int | None] = mapped_column(
        ForeignKey("investment_mandates.id"),
        nullable=True,
        index=True,
    )

    pipeline_stage: Mapped[str] = mapped_column(
        String(50),
        default="sourced",
        nullable=False,
        index=True,
    )

    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_channel: Mapped[str | None] = mapped_column(String(100), nullable=True)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    next_action_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    pass_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
