from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    email_draft_id: Mapped[int] = mapped_column(
        ForeignKey("email_drafts.id"),
        nullable=False,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    reviewer_role: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )