from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class EmailDraft(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "email_drafts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    agent_run_id: Mapped[int] = mapped_column(
        ForeignKey("agent_runs.id"),
        nullable=False,
        index=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending_approval",
        nullable=False,
        index=True,
    )

    tone: Mapped[str] = mapped_column(
        String(50),
        default="professional",
        nullable=False,
    )

    recipient_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    recipient_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    generated_by: Mapped[str] = mapped_column(
        String(50),
        default="template",
        nullable=False,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    prompt_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    evidence_refs: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )