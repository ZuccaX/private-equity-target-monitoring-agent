from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Feedback(TimestampMixin, Base):
    __tablename__ = "feedback"

    __table_args__ = (
        CheckConstraint(
            "feedback_type IN ('rag_relevance', 'trigger_accuracy', 'score_quality', "
            "'recommended_action', 'email_quality', 'overall_run')",
            name="ck_feedback_type",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="ck_feedback_rating",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=True, index=True
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_helpful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extra_data: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
