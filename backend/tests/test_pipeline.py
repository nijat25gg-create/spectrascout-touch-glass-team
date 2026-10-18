from uuid import UUID

import pytest

from app.adapters import cs1, cs3
from app.pipeline.assess import merge_ranked, run_assessment, run_recalculate
from app.schemas.assessment import (
    AssessRequest,
    Claim,
    ExplainInput,
    Explanation,
    ExtractInput,
    MethodRationale,
    RecomputeRequest,
    ScoreInput,
)

from tests._examples import TEXT, example


class RecordingExtraction:
    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.payloads: list[ExtractInput] = []

    def extract(self, payload: ExtractInput):
        self.order.append("extract")
        self.payloads.append(payload)
        return cs1.extract(payload)


class RecordingScoring:
    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.payloads: list[ScoreInput] = []

    def score(self, payload: ScoreInput, probs: dict | None = None):
        self.order.append("score")
        self.payloads.append(payload)
        return cs3.score(payload, probs=probs)


class RecordingExplanation:
    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.payloads: list[ExplainInput] = []

    def explain(self, payload: ExplainInput):
        self.order.append("explain")
        self.payloads.append(payload)
        return cs1.explain(payload)


class FailingExtraction:
    def extract(self, payload: ExtractInput):
        raise AssertionError("extraction must not run during recalculation")


def test_assessment_runs_extract_then_score_then_explain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JEV_LIVE", "0")   # asserts the attributes unchanged; live Jev may lower them
    order: list[str] = []
    extraction = RecordingExtraction(order)
    scoring = RecordingScoring(order)
    explanation = RecordingExplanation(order)

    briefing = run_assessment(
        AssessRequest(text=TEXT, language="de"),
        extraction=extraction,
        scoring=scoring,
        explanation=explanation,
    )

    assert order == ["extract", "score", "explain"]
    case_id = extraction.payloads[0].case_id
    UUID(case_id)
    assert extraction.payloads[0].text == TEXT
    assert extraction.payloads[0].language == "de"
    assert scoring.payloads[0].case_id == case_id
    assert set(scoring.payloads[0].model_dump()) == {"case_id", "features", "attributes", "facts_b"}
    assert scoring.payloads[0].attributes == cs1.extract(extraction.payloads[0]).attributes
    assert scoring.payloads[0].features == explanation.payloads[0].features
    assert explanation.payloads[0].case_id == case_id
    assert explanation.payloads[0].summary == example("C3_extraction")["summary"]
    assert explanation.payloads[0].parameters == cs1.extract(extraction.payloads[0]).parameters
    assert explanation.payloads[0].scoring.rules_version.startswith("rules-")
    assert briefing.case_id == case_id
    assert briefing.schema_version == "0.2"
    assert briefing.language == "de"
    assert briefing.summary == example("C3_extraction")["summary"]
    assert briefing.questions[0].answer is None
    assert briefing.methods.ranked[0].method == "nir"
    assert briefing.methods.ranked[0].claims
    assert "uv_vis" in {r.method for r in briefing.methods.rejected}
    assert briefing.meta.recomputed is False
    assert briefing.meta.rules_version.startswith("rules-")
    assert briefing.expert_flags == []
    assert briefing.changes == []


def test_missing_rationale_does_not_reuse_another_method() -> None:
    extracted = cs1.extract(ExtractInput(case_id="case-1", text=TEXT, language="en"))
    scored = cs3.score(ScoreInput(case_id="case-1", features=extracted.features))
    explained = cs1.explain(
        ExplainInput(
            case_id="case-1",
            language="en",
            summary=extracted.summary,
            parameters=extracted.parameters,
            features=extracted.features,
            scoring=scored,
        )
    )
    explained = explained.model_copy(
        update={
            "rationale": [
                MethodRationale(
                    method="raman",
                    claims=[Claim(claim="Other method.", kb_card="other-card")],
                ),
                MethodRationale(
                    method="nir",
                    claims=[Claim(claim="First NIR claim.", kb_card="first")],
                ),
                MethodRationale(
                    method="nir",
                    claims=[Claim(claim="Second NIR claim.", kb_card="second")],
                ),
            ]
        }
    )

    ranked = merge_ranked(scored, explained)

    assert ranked[0].method == "nir"
    assert ranked[0].claims[0].claim == "First NIR claim."
    assert [item.claim for item in ranked[0].claims] == ["First NIR claim."]

    empty = merge_ranked(
        scored,
        explained.model_copy(
            update={
                "rationale": [
                    MethodRationale(
                        method="raman",
                        claims=[Claim(claim="Other method.", kb_card="other-card")],
                    )
                ]
            }
        ),
    )
    assert empty[0].method == "nir"
    assert empty[0].claims == []


def test_recalculate_skips_extraction_and_keeps_the_case_id(monkeypatch: pytest.MonkeyPatch) -> None:
    briefing = run_assessment(AssessRequest(text=TEXT, language="en"))
    monkeypatch.setattr(cs1, "extract", FailingExtraction().extract)
    order: list[str] = []
    scoring = RecordingScoring(order)
    explanation = RecordingExplanation(order)

    updated = run_recalculate(
        RecomputeRequest(
            briefing=briefing,
            edits=[{"feature": "phase", "value": "liquid", "note": "expert edit"}],
            answers=[
                {
                    "question_id": "q1",
                    "answer": "±0.2 %",
                    "feature_value": "high_precision",
                }
            ],
        ),
        scoring=scoring,
        explanation=explanation,
    )

    assert order == ["score", "explain"]
    assert "extract" not in order
    assert updated.case_id == briefing.case_id
    assert updated.meta.recomputed is True
    assert updated.summary == briefing.summary
    assert updated.parameters == briefing.parameters
    assert scoring.payloads[0].case_id == briefing.case_id
    assert scoring.payloads[0].features.phase.value == "liquid"
    assert scoring.payloads[0].features.accuracy_need.value == "high_precision"
    assert explanation.payloads[0].features.phase.value == "liquid"
    assert [ch.field for ch in updated.changes] == ["features.phase", "features.accuracy_need"]
    assert updated.changes[0].before == briefing.features.phase.value
    assert updated.changes[0].after == "liquid"
    assert updated.questions[0].answer is None


def test_recalculate_rejects_a_value_the_feature_does_not_allow() -> None:
    from app.pipeline.errors import EditError

    briefing = run_assessment(AssessRequest(text=TEXT, language="en"))
    with pytest.raises(EditError):
        run_recalculate(RecomputeRequest(
            briefing=briefing,
            edits=[{"feature": "phase", "value": "banana", "note": None}],
            answers=[],
        ))


def test_step_failure_becomes_the_contract_error_code() -> None:
    from app.pipeline.errors import IntegrationError

    class Broken:
        def score(self, payload):
            raise RuntimeError("boom")

    with pytest.raises(IntegrationError) as info:
        run_assessment(AssessRequest(text=TEXT, language="en"), scoring=Broken())
    assert info.value.code == "engine_error"
    assert info.value.status == 502
