from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InvestmentMandateBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    target_sectors: list[str] = Field(default_factory=list, max_length=100)
    excluded_sectors: list[str] = Field(default_factory=list, max_length=100)
    target_countries: list[str] = Field(default_factory=list, max_length=100)
    revenue_min: float | None = Field(default=None, ge=0)
    revenue_max: float | None = Field(default=None, ge=0)
    ebitda_min: float | None = None
    ebitda_max: float | None = None
    growth_min: float | None = None
    growth_max: float | None = None
    ticket_size_min: float | None = Field(default=None, ge=0)
    ticket_size_max: float | None = Field(default=None, ge=0)
    preferred_business_models: list[str] = Field(default_factory=list, max_length=100)
    is_active: bool = True

    @field_validator(
        "target_sectors",
        "excluded_sectors",
        "target_countries",
        "preferred_business_models",
    )
    @classmethod
    def normalize_list_values(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]
        return list(dict.fromkeys(normalized))

    @model_validator(mode="after")
    def validate_ranges(self) -> Self:
        ranges = (
            ("revenue", self.revenue_min, self.revenue_max),
            ("ebitda", self.ebitda_min, self.ebitda_max),
            ("growth", self.growth_min, self.growth_max),
            ("ticket_size", self.ticket_size_min, self.ticket_size_max),
        )

        for label, minimum, maximum in ranges:
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError(f"{label}_min cannot exceed {label}_max")

        return self


class InvestmentMandateCreate(InvestmentMandateBase):
    pass


class InvestmentMandateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    target_sectors: list[str] | None = None
    excluded_sectors: list[str] | None = None
    target_countries: list[str] | None = None
    revenue_min: float | None = Field(default=None, ge=0)
    revenue_max: float | None = Field(default=None, ge=0)
    ebitda_min: float | None = None
    ebitda_max: float | None = None
    growth_min: float | None = None
    growth_max: float | None = None
    ticket_size_min: float | None = Field(default=None, ge=0)
    ticket_size_max: float | None = Field(default=None, ge=0)
    preferred_business_models: list[str] | None = None
    is_active: bool | None = None


class InvestmentMandateRead(InvestmentMandateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
