"""Live Jev stays off unless JEV_LIVE=1. These tests never call OpenRouter."""
import json

from app.pipeline.assess import run_assessment
from app.schemas.assessment import AssessRequest
from llm import jev
from tests._examples import TEXT


def _questions(n: int) -> list[dict]:
    return [
        {"id": f"attr_{i}", "question": f"Which option is attr {i}?", "options": ["yes", "no", "not_stated"]}
        for i in range(n)
    ]


def test_openrouter_maps_choice_answers(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("JEV_MODEL", "typesafe/jev-1.14")
    calls = []

    def post(url, headers, body, timeout):
        calls.append((url, headers, body, timeout))
        if len(calls) == 1:
            answers = {
                name: {
                    "type": "choice",
                    "choice": "yes",
                    "probabilities": {"yes": 0.8, "no": 0.1, "not_stated": 0.1},
                    "confidence": 0.8,
                }
                for name in body["questions"]
            }
            return {"data": {"result": {"answers": answers}}}
        raise TimeoutError("timed out")

    dists = jev.OpenRouterJev(post=post).classify("customer text only", _questions(9), ["DO_NOT_SEND"])

    assert len(calls) == 2
    url, headers, body, timeout = calls[0]
    assert url == jev.JEV_URL
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["Content-Type"] == "application/json"
    assert timeout == jev.JEV_TIMEOUT_S
    assert set(body) == {"model", "state", "questions"}
    assert body["model"] == "typesafe/jev-1.14"
    assert body["state"] == "customer text only"
    assert len(body["questions"]) == jev.JEV_BATCH
    assert body["questions"]["attr_0"] == {
        "type": "choice",
        "instructions": "Which option is attr 0?",
        "criteria": {"yes": "yes", "no": "no", "not_stated": "not_stated"},
    }
    assert "DO_NOT_SEND" not in json.dumps(body)
    assert len(calls[1][2]["questions"]) == 1
    assert set(dists) == {f"attr_{i}" for i in range(8)}
    assert dists["attr_0"] == {"yes": 0.8, "no": 0.1, "not_stated": 0.1}


def _stable(briefing) -> dict:
    data = briefing.model_dump(mode="json")
    data.pop("case_id")
    data["meta"].pop("generated_at")
    return data


def test_http_error_returns_empty_and_briefing_is_unchanged(monkeypatch) -> None:
    monkeypatch.delenv("JEV_LIVE", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    calls = {"n": 0}

    def post(url, headers, body, timeout):
        calls["n"] += 1
        raise TimeoutError("timed out")

    monkeypatch.setattr(jev, "_post", post)
    baseline = run_assessment(AssessRequest(text=TEXT, language="de"))
    assert calls["n"] == 0

    monkeypatch.setenv("JEV_LIVE", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    failed = run_assessment(AssessRequest(text=TEXT, language="de"))

    assert calls["n"] == (len(jev.questions()) + jev.JEV_BATCH - 1) // jev.JEV_BATCH
    assert _stable(failed) == _stable(baseline)
