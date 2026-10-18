"""Run extraction, scoring, and explanation, then assemble one C8 briefing.

Recalculation starts at scoring. A failed step becomes IntegrationError with the
contract code (llm_error / engine_error). The original exception is logged and is
not copied into the public message.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


from app.adapters import cs1, cs3
from app.pipeline.errors import IntegrationError
from app.pipeline.placeholders import expert_flags, kb_version, model_name
from app.pipeline.ports import ExplanationPort, ExtractionPort, ScoringPort
from app.pipeline.recompute import apply_recompute_updates
from app.schemas.assessment import (
    AssessmentResponse,
    AssessRequest,
    Change,
    Claim,
    ExplainInput,
    Explanation,
    ExtractInput,
    Features,
    Meta,
    Methods,
    Parameter,
    Question,
    RankedMethod,
    RecomputeRequest,
    ScoreInput,
    Scoring,
)

logger = logging.getLogger(__name__)

Language = Literal["en", "de"]


def run_assessment(
    request: AssessRequest,
    *,
    extraction: ExtractionPort = cs1,
    scoring: ScoringPort = cs3,
    explanation: ExplanationPort = cs1,
) -> AssessmentResponse:
    return _run_assessment(request, extraction, scoring, explanation)


def run_recalculate(
    request: RecomputeRequest,
    *,
    scoring: ScoringPort = cs3,
    explanation: ExplanationPort = cs1,
) -> AssessmentResponse:
    """Score and explain again. Extraction is not called."""
    return _run_recalculate(request, scoring, explanation)


def _step(code, label, fn, payload):
    """Run one pipeline step and turn any failure into IntegrationError with the contract code."""
    try:
        return fn(payload)
    except IntegrationError:
        raise
    except TimeoutError:
        logger.exception("%s timed out", label)
        raise IntegrationError(code, f"{label} timed out.", status=504) from None
    except Exception:  # noqa: BLE001  (the original error is logged, not sent to the browser)
        logger.exception("%s failed", label)
        raise IntegrationError(code, f"{label} returned an unusable result.") from None


def _jev_live() -> bool:
    return os.getenv("JEV_LIVE", "").strip().lower() in {"1", "true", "yes"}


def _cross_check_jev(text: str, extracted):
    """After extract, before score, and only when JEV_LIVE=1.

    Jev may lower attribute confidence and weight question strength. It does not rank methods.
    A failure leaves the extraction untouched and passes no probabilities.
    """
    if not _jev_live():
        return extracted, None
    try:
        from llm import jev

        attributes = list(extracted.attributes or [])
        dists = jev.OpenRouterJev().classify(text, jev.questions(), attributes)
        if not dists:
            return extracted, None
        facts, votes, notes = jev.merge(attributes, dists)
        for note in notes:
            logger.info("jev %s", note)
        logger.info("jev votes=%s agree=%s", len(votes), sum(1 for vote in votes if vote.agrees))
        update = {"attributes": facts}
        if votes:
            update["jev"] = votes
        return extracted.model_copy(update=update), jev.distributions_for_voi(dists) or None
    except Exception:
        logger.warning("jev cross-check skipped")
        return extracted, None


def resolve_language(language: Language | None) -> Language:
    """Use the requested language. An omitted language stays English."""
    if language is None:
        return "en"
    return language


def _run_assessment(
    request: AssessRequest,
    extraction: ExtractionPort,
    scoring: ScoringPort,
    explanation: ExplanationPort,
) -> AssessmentResponse:
    language = resolve_language(request.language)
    case_id = str(uuid4())
    extracted = _step(
        "llm_error", "Parameter extraction", extraction.extract,
        ExtractInput(case_id=case_id, text=request.text, language=language),
    )
    extracted, probs = _cross_check_jev(request.text, extracted)
    score_input = ScoreInput(case_id=case_id, features=extracted.features, attributes=extracted.attributes,
                             facts_b=getattr(extracted, "facts_b", None))
    # No probs argument unless Jev actually returned distributions, so the score port stays as today.
    score = (lambda payload: scoring.score(payload, probs=probs)) if probs else scoring.score
    scored = _step("engine_error", "Rules engine", score, score_input)
    explained = _step(
        "llm_error", "Explanation", explanation.explain,
        ExplainInput(
            case_id=case_id,
            language=language,
            summary=extracted.summary,
            parameters=extracted.parameters,
            features=extracted.features,
            scoring=scored,
        ),
    )
    return assemble(
        case_id=case_id,
        language=language,
        summary=extracted.summary,
        parameters=extracted.parameters,
        features=extracted.features,
        scoring=scored,
        explanation=explained,
        changes=[],
        recomputed=False,
        attributes=extracted.attributes,
        facts_b=getattr(extracted, "facts_b", None),
    )


def _run_recalculate(
    request: RecomputeRequest,
    scoring: ScoringPort,
    explanation: ExplanationPort,
) -> AssessmentResponse:
    briefing = request.briefing
    features, changes = apply_recompute_updates(briefing, request.edits, request.answers)
    scored = _step(
        "engine_error", "Rules engine", scoring.score,
        # gates engine: recompute from the posted (possibly edited) attributes, never echo the old assessment
        ScoreInput(case_id=briefing.case_id, features=features, attributes=briefing.attributes,
                   facts_b=getattr(briefing, "facts_b", None)),
    )
    explained = _step(
        "llm_error", "Explanation", explanation.explain,
        ExplainInput(
            case_id=briefing.case_id,
            language=briefing.language,
            summary=briefing.summary,
            parameters=briefing.parameters,
            features=features,
            scoring=scored,
        ),
    )
    updated = assemble(
        case_id=briefing.case_id,
        language=briefing.language,
        summary=briefing.summary,
        parameters=briefing.parameters,
        features=features,
        scoring=scored,
        explanation=explained,
        changes=changes,
        recomputed=True,
        attributes=briefing.attributes,
        facts_b=getattr(briefing, "facts_b", None),
    )
    answers = {question.id: question.answer for question in briefing.questions}
    return updated.model_copy(
        update={
            "questions": [
                question.model_copy(update={"answer": answers.get(question.id)})
                for question in updated.questions
            ]
        }
    )


def _facts_b_from(scoring: Scoring):
    """Step A gave no facts_b (mock, EXTRACT_B=0): expose the facts engine B used, so they stay editable."""
    from engine.score import facts_b_from_assessment
    return facts_b_from_assessment(getattr(scoring, "assessment_b", None))


def assemble(
    *,
    case_id: str,
    language: Language,
    summary: str,
    parameters: list[Parameter],
    features: Features,
    scoring: Scoring,
    explanation: Explanation,
    changes: list[Change],
    recomputed: bool,
    attributes=None,
    facts_b=None,
) -> AssessmentResponse:
    return AssessmentResponse(
        schema_version="0.2",
        case_id=case_id,
        language=language,
        summary=summary,
        parameters=parameters,
        features=features,
        questions=[
            Question.model_validate({**question.model_dump(), "answer": None})
            for question in explanation.questions
        ],
        methods=Methods(
            ranked=merge_ranked(scoring, explanation),
            rejected=list(scoring.rejected),
        ),
        experiment=explanation.experiment,
        risks=list(explanation.risks),
        expert_flags=expert_flags(),
        changes=changes,
        meta=Meta(
            model=model_name(),
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            rules_version=scoring.rules_version,
            kb_version=kb_version(),
            recomputed=recomputed,
        ),
        attributes=attributes,                  # v0.3 optional: C3.attributes (None for a v0.2 extraction)
        assessment=scoring.assessment,          # v0.3 optional: full gates result from engine.score_methods
        assessment_b=getattr(scoring, "assessment_b", None),   # v0.4 optional: method B engine result
        facts_b=facts_b or _facts_b_from(scoring),             # v0.4 optional: method B facts (editable)
    )


def merge_ranked(scoring: Scoring, explanation: Explanation) -> list[RankedMethod]:
    """Attach claims by method. A missing match gets an empty claim list.

    The first rationale entry for a method wins. Another method's claims
    are never reused.
    """
    claims_by_method: dict[str, list[Claim]] = {}
    for item in explanation.rationale:
        claims_by_method.setdefault(item.method, item.claims)
    return [
        RankedMethod.model_validate(
            {**method.model_dump(), "claims": claims_by_method.get(method.method, [])}
        )
        for method in scoring.ranked
    ]
