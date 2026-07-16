import pytest
from pydantic import ValidationError

from app.schemas.feedback import FeedbackCreate
from app.schemas.mandate import InvestmentMandateCreate
from app.schemas.news_article import NewsArticleRead
from app.schemas.pipeline import CompanyPipelineUpdate


def test_mandate_normalizes_lists_and_accepts_valid_ranges() -> None:
    mandate = InvestmentMandateCreate(
        name="European Software",
        target_sectors=[" SaaS ", "SaaS", "Data"],
        revenue_min=10.0,
        revenue_max=100.0,
    )

    assert mandate.target_sectors == ["SaaS", "Data"]


def test_mandate_rejects_reversed_range() -> None:
    with pytest.raises(ValidationError, match="revenue_min"):
        InvestmentMandateCreate(
            name="Invalid",
            revenue_min=100.0,
            revenue_max=10.0,
        )


def test_feedback_requires_a_value() -> None:
    with pytest.raises(ValidationError, match="At least one"):
        FeedbackCreate(feedback_type="overall_run")


def test_feedback_accepts_bounded_rating() -> None:
    feedback = FeedbackCreate(
        feedback_type="score_quality",
        rating=5,
    )

    assert feedback.rating == 5


def test_pipeline_rejects_unknown_stage() -> None:
    with pytest.raises(ValidationError):
        CompanyPipelineUpdate(pipeline_stage="unknown")  # type: ignore[arg-type]


def test_news_schema_exposes_milestone_three_lifecycle() -> None:
    assert {
        "trigger_extraction_status",
        "trigger_extracted_at",
        "trigger_extraction_version",
    } <= set(NewsArticleRead.model_fields)
