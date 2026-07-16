import math
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.services.trigger_providers.base import TriggerCandidate


def test_candidate_derives_negative_server_side() -> None:
    candidate = TriggerCandidate(
        trigger_type="customer_loss",
        title="Loss",
        evidence_sentence="A customer left.",
        confidence_score=0.8,
        event_date=datetime.now(timezone.utc),
        extraction_method="rules",
    )
    assert candidate.is_negative is True


def test_candidate_rejects_unknown_type_negative_override_and_nonfinite() -> None:
    base = {
        "trigger_type": "customer_win",
        "title": "Win",
        "evidence_sentence": "A customer joined.",
        "confidence_score": 0.8,
        "event_date": datetime.now(timezone.utc),
        "extraction_method": "rules",
    }
    with pytest.raises(ValidationError):
        TriggerCandidate.model_validate({**base, "trigger_type": "unknown"})
    with pytest.raises(ValidationError):
        TriggerCandidate.model_validate({**base, "is_negative": True})
    with pytest.raises(ValidationError):
        TriggerCandidate.model_validate({**base, "confidence_score": math.nan})
