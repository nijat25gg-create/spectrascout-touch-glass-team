"""CS1 and CS3 adapters call llm/ and engine/ directly (LLM_MOCK=1 in tests)."""
import pytest

from app.adapters import cs1, cs3
from app.schemas.assessment import ExplainInput, ExtractInput, ScoreInput
from tests._examples import TEXT, example


def _extract_input() -> ExtractInput:
    return ExtractInput(case_id="case-1", text=TEXT, language="de")


def test_cs1_extract_returns_c3_with_all_16_parameters() -> None:
    result = cs1.extract(_extract_input())
    assert result.summary
    assert len(result.parameters) == 16
    assert result.features.phase.value == example("C3_extraction")["features"]["phase"]["value"]


def test_cs3_score_runs_the_rules_engine() -> None:
    extracted = cs1.extract(_extract_input())
    result = cs3.score(ScoreInput(case_id="case-1", features=extracted.features))
    assert result.rules_version.startswith("rules-")
    assert result.ranked[0].method == "nir"
    assert all(s.rule_id for s in result.ranked[0].scores)
    assert {r.method for r in result.rejected} >= {"uv_vis"}


def test_cs1_explain_returns_c7_for_the_ranked_methods() -> None:
    extracted = cs1.extract(_extract_input())
    scored = cs3.score(ScoreInput(case_id="case-1", features=extracted.features))
    result = cs1.explain(ExplainInput(
        case_id="case-1", language="de", summary=extracted.summary,
        parameters=extracted.parameters, features=extracted.features, scoring=scored,
    ))
    assert result.questions
    assert {r.method for r in result.rationale} & {m.method for m in scored.ranked}


def test_adapters_reject_the_wrong_model() -> None:
    with pytest.raises(TypeError):
        cs1.extract(ScoreInput.model_validate(example("C4_score_input")))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        cs3.score(_extract_input())  # type: ignore[arg-type]
