from typing import Any

from sqlalchemy import Boolean, CheckConstraint, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class InvestmentMandate(TimestampMixin, Base):
    __tablename__ = "investment_mandates"

    __table_args__ = (
        CheckConstraint(
            "revenue_min IS NULL OR revenue_max IS NULL OR revenue_min <= revenue_max",
            name="ck_investment_mandates_revenue_range",
        ),
        CheckConstraint(
            "ebitda_min IS NULL OR ebitda_max IS NULL OR ebitda_min <= ebitda_max",
            name="ck_investment_mandates_ebitda_range",
        ),
        CheckConstraint(
            "ticket_size_min IS NULL OR ticket_size_max IS NULL OR "
            "ticket_size_min <= ticket_size_max",
            name="ck_investment_mandates_ticket_range",
        ),
        CheckConstraint(
            "growth_min IS NULL OR growth_max IS NULL OR growth_min <= growth_max",
            name="ck_investment_mandates_growth_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_sectors: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    excluded_sectors: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    target_countries: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    revenue_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    ebitda_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    ebitda_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    ticket_size_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    ticket_size_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_business_models: Mapped[list[str]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
