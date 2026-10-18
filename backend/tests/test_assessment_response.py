import pytest
from pydantic import ValidationError

from app.schemas.assessment import AssessmentResponse
from tests._examples import example


def test_briefing_v0_2_example_is_valid() -> None:
    parsed = AssessmentResponse.model_validate(example("C8_briefing"))
    assert parsed.schema_version == "0.2"
    assert parsed.methods.ranked[0].claims


def test_briefing_rejects_a_missing_section_and_extra_field() -> None:
    missing = example("C8_briefing")
    del missing["features"]
    with pytest.raises(ValidationError):
        AssessmentResponse.model_validate(missing)
    extra = example("C8_briefing")
    extra["recommended_methods"] = []
    with pytest.raises(ValidationError):
        AssessmentResponse.model_validate(extra)


def test_change_uses_the_contract_shape() -> None:
    data = example("C8_briefing")
    data["changes"] = [{"field": "features.phase", "before": "unknown", "after": "liquid"}]
    AssessmentResponse.model_validate(data)
    data["changes"] = [{"feature": "phase", "value": "liquid", "note": "x"}]
    with pytest.raises(ValidationError):
        AssessmentResponse.model_validate(data)
