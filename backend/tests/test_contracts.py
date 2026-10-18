"""The backend uses the shared contract models from contracts/models.py, not a copy."""
import pytest
from pydantic import ValidationError

import contracts.models as c
from app.schemas import assessment as s
from app.schemas.errors import ErrorResponse
from tests._examples import TEXT, example


def test_backend_names_are_the_shared_contract_models() -> None:
    assert s.AssessmentResponse is c.Briefing
    assert s.Extraction is c.Extraction
    assert s.Scoring is c.Scoring
    assert s.Explanation is c.Explanation
    assert s.RecomputeRequest is c.RecomputeRequest
    assert s.Change is c.Change
    assert ErrorResponse is c.ErrorResponse


@pytest.mark.parametrize(
    "name, model",
    [
        ("C2_extract_input", c.ExtractInput),
        ("C3_extraction", c.Extraction),
        ("C4_score_input", c.ScoreInput),
        ("C5_scoring", c.Scoring),
        ("C6_explain_input", c.ExplainInput),
        ("C7_explanation", c.Explanation),
        ("C8_briefing", c.Briefing),
        ("C1b_recompute_request", c.RecomputeRequest),
        ("E_error_response", c.ErrorResponse),
    ],
)
def test_contract_examples_validate(name: str, model) -> None:
    model.model_validate(example(name))


def test_c1_request_strips_text_and_enforces_length() -> None:
    parsed = s.AssessRequest.model_validate({"text": f"  {TEXT}  ", "language": "de"})
    assert parsed.text == TEXT
    assert s.AssessRequest(text="x" * 20).language is None
    assert s.AssessRequest(text="x" * 5000).text == "x" * 5000
    for bad in ({"text": "x" * 19}, {"text": "   "}, {"text": TEXT, "language": "fr"},
                {"text": TEXT, "title": "case"}):
        with pytest.raises(ValidationError):
            s.AssessRequest.model_validate(bad)


def test_features_only_accept_allowed_values() -> None:
    data = example("C3_extraction")
    data["features"]["phase"]["value"] = "banana"
    with pytest.raises(ValidationError):
        c.Extraction.model_validate(data)


def test_c4_rejects_parameters_and_c5_rejects_claims() -> None:
    bad = example("C4_score_input")
    bad["parameters"] = []
    with pytest.raises(ValidationError):
        c.ScoreInput.model_validate(bad)
    with_claims = example("C5_scoring")
    with_claims["ranked"][0]["claims"] = []
    with pytest.raises(ValidationError):
        c.Scoring.model_validate(with_claims)


def test_c7_question_has_no_answer_but_c8_question_has() -> None:
    with_answer = example("C7_explanation")
    with_answer["questions"][0]["answer"] = None
    with pytest.raises(ValidationError):
        c.Explanation.model_validate(with_answer)
    briefing = c.Briefing.model_validate(example("C8_briefing"))
    assert all(hasattr(q, "answer") for q in briefing.questions)
