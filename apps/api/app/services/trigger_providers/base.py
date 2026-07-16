from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

PositiveTriggerType = Literal[
    "market_expansion",
    "product_launch",
    "partnership",
    "customer_win",
    "funding",
    "leadership_hire",
    "acquisition",
]
NegativeTriggerType = Literal[
    "layoffs",
    "profit_warning",
    "customer_loss",
    "regulatory_issue",
    "management_departure",
    "cyber_incident",
    "litigation",
]
CanonicalTriggerType = PositiveTriggerType | NegativeTriggerType

POSITIVE_TRIGGER_TYPES = frozenset(
    {
        "market_expansion",
        "product_launch",
        "partnership",
        "customer_win",
        "funding",
        "leadership_hire",
        "acquisition",
    }
)
NEGATIVE_TRIGGER_TYPES = frozenset(
    {
        "layoffs",
        "profit_warning",
        "customer_loss",
        "regulatory_issue",
        "management_departure",
        "cyber_incident",
        "litigation",
    }
)
CANONICAL_TRIGGER_TYPES = POSITIVE_TRIGGER_TYPES | NEGATIVE_TRIGGER_TYPES


class TriggerCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trigger_type: CanonicalTriggerType
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5_000)
    confidence_score: float = Field(ge=0, le=1, allow_inf_nan=False)
    evidence_sentence: str = Field(min_length=1, max_length=2_000)
    event_date: datetime
    extraction_method: Literal["rules", "llm", "hybrid"]

    @field_validator("event_date")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("event_date must be timezone-aware")
        return value

    @property
    def is_negative(self) -> bool:
        return self.trigger_type in NEGATIVE_TRIGGER_TYPES


class TriggerProviderResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: tuple[TriggerCandidate, ...] = ()
    fallbacks: tuple[str, ...] = ()


class TriggerProvider(Protocol):
    def extract(self, article) -> list[TriggerCandidate]: ...
