from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.pipeline.assess import run_assessment
from app.pipeline.errors import IntegrationError
from app.schemas.assessment import AssessmentResponse, AssessRequest

client = TestClient(app)
from tests._examples import TEXT, example


def test_assess_request_accepts_english_and_german() -> None:
    english = AssessRequest(text=TEXT, language="en")
    german = AssessRequest(text="Feuchte im Polymer messen.", language="de")
    omitted = AssessRequest(text=TEXT)

    assert english.language == "en"
    assert german.language == "de"
    assert omitted.language is None


def test_assess_request_strips_text_and_allows_null_language() -> None:
    assessment = AssessRequest.model_validate({"text": f"  {TEXT}  ", "language": None})

    assert assessment.text == TEXT
    assert assessment.language is None


def test_assess_request_rejects_blank_unknown_language_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        AssessRequest(text="   ")

    with pytest.raises(ValidationError):
        AssessRequest(text="x" * 19)

    with pytest.raises(ValidationError):
        AssessRequest(text="x" * 5001)

    with pytest.raises(ValidationError):
        AssessRequest(text=TEXT, language="fr")

    with pytest.raises(ValidationError):
        AssessRequest(text=TEXT, language="EN")

    with pytest.raises(ValidationError):
        AssessRequest.model_validate({"text": TEXT, "title": "case"})


def test_assess_request_accepts_text_at_the_length_limits() -> None:
    assert len(AssessRequest(text="x" * 20).text) == 20
    assert len(AssessRequest(text="x" * 5000).text) == 5000


def test_create_assessment_returns_the_briefing() -> None:
    response = client.post(
        "/assessments",
        json={"text": f"  {TEXT}  ", "language": "de"},
    )

    assert response.status_code == 200
    briefing = AssessmentResponse.model_validate(response.json())
    UUID(briefing.case_id)
    assert briefing.schema_version == "0.2"
    assert briefing.summary == example("C3_extraction")["summary"]
    assert briefing.language == "de"
    assert briefing.parameters[0].id == "measurand"
    assert briefing.features.phase.value == "solid_powder"
    assert briefing.methods.ranked[0].method == "nir"
    assert briefing.methods.ranked[0].claims
    assert "uv_vis" in {r.method for r in briefing.methods.rejected}
    assert briefing.questions[0].text
    assert briefing.questions[0].answer is None
    assert briefing.meta.recomputed is False
    assert briefing.changes == []


def test_create_assessment_defaults_omitted_language_to_english() -> None:
    response = client.post("/assessments", json={"text": TEXT})

    assert response.status_code == 200
    assert response.json()["language"] == "en"


def test_create_assessment_returns_the_validation_envelope_for_short_text() -> None:
    response = client.post("/assessments", json={"text": "too short", "language": "en"})

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "The request is invalid.",
            "details": "text: min_length=20",
        }
    }


def test_create_assessment_rejects_extra_fields_with_the_validation_envelope() -> None:
    response = client.post("/assessments", json={"text": TEXT, "title": "case"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "detail" not in body
    assert "title" in body["error"]["details"]


def test_pipeline_failure_returns_the_stable_error_body(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(assessment: AssessRequest) -> AssessmentResponse:
        raise IntegrationError(
            "llm_error",
            "The assessment pipeline returned an unusable result.",
        )

    monkeypatch.setattr("app.api.assessments.run_assessment", fail)
    response = client.post("/assessments", json={"text": TEXT})

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "llm_error",
            "message": "The assessment pipeline returned an unusable result.",
            "details": "",
        }
    }


def test_pipeline_timeout_returns_504(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(assessment: AssessRequest) -> AssessmentResponse:
        raise IntegrationError("llm_error", "The assessment pipeline timed out.", status=504)

    monkeypatch.setattr("app.api.assessments.run_assessment", fail)
    response = client.post("/assessments", json={"text": TEXT})

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "llm_error"
    assert set(response.json()) == {"error"}


def test_recalculate_returns_the_same_briefing_model() -> None:
    created = client.post("/assessments", json={"text": TEXT, "language": "en"})
    briefing = created.json()
    response = client.post(
        "/assessments/recalculate",
        json={
            "briefing": briefing,
            "edits": [{"feature": "water_level", "value": "high", "note": "lab"}],
            "answers": [],
        },
    )

    assert response.status_code == 200
    updated = AssessmentResponse.model_validate(response.json())
    assert updated.schema_version == "0.2"
    assert updated.case_id == briefing["case_id"]
    assert updated.meta.recomputed is True
    assert updated.features.water_level.value == "high"
    assert updated.changes[0].field == "features.water_level"
    paths = client.get("/openapi.json").json()["paths"]
    assert "/assessments" in paths
    assert "/assessments/recalculate" in paths
    assert "/api/assessments" not in paths


def test_recalculate_accepts_the_briefing_the_page_posts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENGINE", "ab")   # asserts the gates rejection of mir (ENGINE=b is the default)
    created = client.post("/assessments", json={"text": TEXT, "language": "en"})
    briefing = created.json()
    temp = next(p for p in briefing["parameters"] if p["id"] == "temperature")
    temp.update(value="200 °C", status="known", source="expert_edit")
    briefing["questions"][0]["answer"] = "about 60 C"      # free text: no feature value
    briefing["questions"][1]["answer"] = "long"           # dropdown value for distance_class

    response = client.post("/assessments/recalculate", json=briefing)

    assert response.status_code == 200
    updated = AssessmentResponse.model_validate(response.json())
    assert updated.case_id == briefing["case_id"]
    assert updated.meta.recomputed is True
    assert updated.summary == briefing["summary"]
    temperature = next(item for item in updated.parameters if item.id == "temperature")
    assert temperature.value == "200 °C"
    assert temperature.source == "expert_edit"
    assert updated.questions[0].answer == "about 60 C"
    assert updated.features.temperature_class.value == "high"
    assert updated.features.distance_class.value == "long"
    assert [ch.field for ch in updated.changes] == ["features.temperature_class", "features.distance_class"]
    assert "mir" in {r.method for r in updated.methods.rejected}
