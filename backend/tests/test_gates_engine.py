"""Gates engine (18.10): C4 carries attributes, C8 carries attributes and assessment, recalculate recomputes."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.assessment import AssessmentResponse
from tests._examples import TEXT

client = TestClient(app)


@pytest.fixture(autouse=True)
def _gates_rank(monkeypatch: pytest.MonkeyPatch) -> None:
    """These tests check the gates engine; since 18.10 ENGINE=b is the default, so pin ab here."""
    monkeypatch.setenv("ENGINE", "ab")


def _assess() -> AssessmentResponse:
    r = client.post("/assessments", json={"text": TEXT, "language": "de"})
    assert r.status_code == 200, r.text
    return AssessmentResponse.model_validate(r.json())


def test_ranking_comes_from_the_gates_and_reaches_c8() -> None:
    b = _assess()
    assert b.meta.rules_version.startswith("rules-gates")
    assert b.attributes and len(b.attributes) == 34
    assert b.assessment is not None and b.assessment.decision_status == "provisional"
    # ranked/rejected are filled from the same gates result
    top_rows = b.assessment.selected
    assert b.methods.ranked[0].method == "nir" and top_rows[0] == "K03"
    assert {r.method for r in b.methods.ranked}.isdisjoint({r.method for r in b.methods.rejected})


def test_recalculate_recomputes_from_edited_attributes() -> None:
    b = _assess()
    edited = [a.model_copy(update={"value": "gas", "status": "known", "quote": None})
              if a.name == "sample_form" else a for a in b.attributes]
    posted = b.model_copy(update={"attributes": edited})
    r = client.post("/assessments/recalculate", json={"briefing": posted.model_dump(mode="json"),
                                                      "edits": [], "answers": []})
    assert r.status_code == 200, r.text
    after = AssessmentResponse.model_validate(r.json())
    assert after.assessment.decision_status == "outside_scope"   # gas is outside the catalog
    assert after.methods.ranked == []                               # nothing recommended outside scope
    assert after.attributes == edited
