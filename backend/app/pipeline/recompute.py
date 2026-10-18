"""Apply C1b edits and answers to a briefing's features.

Every new value must be one of the allowed values of that feature (contracts/models.py),
otherwise EditError (→ 422). Each change is reported as C8 `changes` {field, before, after}.
"""
from typing import get_args

import app  # noqa: F401
from contracts import models as c
from engine.numeric import classify

from app.pipeline.errors import EditError
from app.schemas.assessment import (
    AssessmentResponse,
    Change,
    FeatureEdit,
    Features,
    QuestionAnswer,
    RecomputeRequest,
)


def allowed_values(feature: str) -> tuple[str, ...]:
    field = Features.model_fields.get(feature)
    if field is None:
        return ()
    value_type = field.annotation.model_fields["value"].annotation
    return get_args(value_type)


def request_from_briefing(briefing: AssessmentResponse) -> RecomputeRequest:
    """Build C1b from the briefing the page posts.

    - A parameter the expert edited ("80 °C") becomes a feature edit through engine.numeric
      (temperature, pressure, distance, concentration, water content).
    - An answered question with a `feature` sets that feature, but only when the answer is
      one of its allowed values (the dropdown). Free text stays an answer without a feature value.
    """
    edits: list[FeatureEdit] = []
    for p in briefing.parameters:
        if p.source != "expert_edit" or not p.value:
            continue
        hit = classify(p.id, p.value)
        if hit:
            feature, value = hit
            edits.append(FeatureEdit(feature=feature, value=value, note=f"{p.id}: {p.value}"))
    answers = []
    for q in briefing.questions:
        if not q.answer:
            continue
        value = q.answer if q.feature and q.answer in allowed_values(q.feature) else None
        answers.append(QuestionAnswer(question_id=q.id, answer=q.answer, feature_value=value))
    return RecomputeRequest(briefing=briefing, edits=edits, answers=answers)


def apply_recompute_updates(
    briefing: AssessmentResponse,
    edits: list[FeatureEdit],
    answers: list[QuestionAnswer],
) -> tuple[Features, list[Change]]:
    data = briefing.features.model_dump()
    questions = {q.id: q for q in briefing.questions}
    changes: list[Change] = []

    def setv(feature: str, value: str) -> None:
        if value not in allowed_values(feature):
            raise EditError(f"{feature}: '{value}' is not an allowed value")
        before = data[feature]["value"]
        if before == value:
            return
        data[feature] = {"value": value, "status": "known"}
        changes.append(Change(field=f"features.{feature}", before=before, after=value))

    for edit in edits:
        setv(edit.feature, edit.value)

    for answer in answers:
        q = questions.get(answer.question_id)
        if q is None:
            raise EditError(f"unknown question_id '{answer.question_id}'")
        if q.feature and answer.feature_value is not None:
            setv(q.feature, answer.feature_value)

    return Features.model_validate(data), changes
