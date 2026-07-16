from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class CRMInteraction(TimestampMixin, Base):
    __tablename__ = "crm_interactions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )

    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.id"),
        nullable=True,
        index=True,
    )

    interaction_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    direction: Mapped[str] = mapped_column(
        String(50),
        default="outbound",
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    sentiment_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        default="mock_crm",
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )