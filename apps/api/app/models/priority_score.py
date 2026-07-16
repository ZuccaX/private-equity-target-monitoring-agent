from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class PriorityScore(TimestampMixin, Base):
    __tablename__ = "priority_scores"

    __table_args__ = (
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_priority_scores_overall_score_range",
        ),
    )

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

    overall_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    score_version: Mapped[str] = mapped_column(
        String(50),
        default="v1",
        nullable=False,
    )

    sector_fit_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    trigger_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    relationship_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    timing_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reasons: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    evidence_refs: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )