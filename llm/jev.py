"""Jev layer for step A (v0.3): a second, independent classifier of the attribute vocabulary.

Role (team decision 17.10): Jev checks step A, it never chooses the method and never adds facts.

    questions()                      -> Jev questions generated from rules/gates.yaml (one per attribute)
    merge(facts, dists, threshold)   -> (facts with statuses adjusted, [JevVote], notes)
    distributions_for_voi(dists)     -> {attribute: {value: p}} without not_stated, for engine questions

Status rule (merge). Jev can only lower confidence, never invent:
- known (verbatim quote): Jev agrees -> known; Jev confidently names another value -> conflicting;
  otherwise known stays (the quote is the evidence) and the vote is recorded.
- assumed: Jev agrees confidently -> assumed (supported); Jev confidently says another value or
  "not_stated" -> unknown, so the attribute becomes a question instead of a hidden assumption.
- unknown / conflicting: unchanged. A confident Jev value only goes into the notes for the expert.

Clients:
- MockJev: deterministic, for tests and the cloud (LLM_MOCK=1). No key, no network.
- OpenRouterJev: live cross-check (JEV_LIVE=1). It never chooses the method. A missing key,
  timeout, or HTTP error returns {} for that batch and does not raise.
"""
import json
import math
import os
import urllib.error
import urllib.request

from contracts.models import AttributeFact, JevVote

from .vocab import vocabulary

NOT_STATED = "not_stated"
THRESHOLD = 0.6   # docs/jev-attributes.md; calibrate on D01-D08 only, never on H


def questions(g: dict | None = None, include_never: bool = True) -> list[dict]:
    """One classification question per attribute; options = vocabulary values + not_stated."""
    out = []
    for name, v in vocabulary(g).items():
        if v["kind"] == "never" and not include_never:
            continue
        out.append({
            "id": name,
            "question": f"Based only on the customer's text, which option describes '{name.replace('_', ' ')}'?",
            "options": v["values"] + [NOT_STATED],
        })
    return out


def _top(dist: dict) -> tuple[str | None, float]:
    if not dist:
        return None, 0.0
    value, p = max(dist.items(), key=lambda kv: kv[1])
    return value, float(p)


def merge(facts: list[AttributeFact], dists: dict, threshold: float = THRESHOLD):
    """dists: {attribute: {option: probability}} from Jev. Returns (facts, votes, notes)."""
    out, votes, notes = [], [], []
    for f in facts:
        dist = dists.get(f.name)
        if not dist:
            out.append(f)
            continue
        top, p = _top(dist)
        jev_value = None if top == NOT_STATED else top
        agrees = jev_value is not None and jev_value == f.value
        votes.append(JevVote(name=f.name, value=jev_value, p=round(p, 3), agrees=agrees))
        confident = p >= threshold
        if f.status == "known":
            if confident and jev_value is not None and not agrees:
                out.append(f.model_copy(update={"status": "conflicting"}))
                notes.append(f"{f.name}: text quote says {f.value!r}, Jev says {jev_value!r} (p={p:.2f}) -> conflicting")
                continue
        elif f.status == "assumed":
            if confident and not agrees:
                out.append(f.model_copy(update={"status": "unknown", "value": None, "quote": None}))
                notes.append(f"{f.name}: assumption {f.value!r} not supported by Jev "
                             f"({jev_value or NOT_STATED}, p={p:.2f}) -> unknown, ask")
                continue
        elif confident and jev_value is not None:
            notes.append(f"{f.name}: step A left it {f.status}, Jev suggests {jev_value!r} (p={p:.2f}); not used")
        out.append(f)
    return out, votes, notes


def distributions_for_voi(dists: dict) -> dict:
    """Jev distributions without not_stated, renormalised. Used to weight question strength:
    strength = sum over values of p(value) * [decision changes]. Missing -> engine uses uniform."""
    out = {}
    for name, dist in (dists or {}).items():
        real = {k: float(v) for k, v in dist.items() if k != NOT_STATED and v > 0}
        total = sum(real.values())
        if total > 0:
            out[name] = {k: v / total for k, v in real.items()}
    return out


JEV_URL = "https://openrouter.ai/api/alpha/decisions"
JEV_DEFAULT_MODEL = "typesafe/jev-1.14"
JEV_BATCH = 8
JEV_TIMEOUT_S = 10


def _batches(items: list, size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _choice_questions(batch: list[dict]) -> dict:
    """Nest choice questions. Only the question text and its options."""
    questions = {}
    for item in batch:
        name = item.get("id")
        options = item.get("options") or []
        if not name or not options:
            continue
        questions[str(name)] = {
            "type": "choice",
            "instructions": item.get("question") or str(name),
            "criteria": {str(option): str(option) for option in options},
        }
    return questions


def _finite(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _probability_map(answer) -> dict | None:
    if not isinstance(answer, dict):
        return None
    raw = answer.get("probabilities")
    if not isinstance(raw, dict):
        return None
    dist = {}
    for option, value in raw.items():
        number = _finite(value)
        if number is not None:
            dist[str(option)] = number
    return dist or None


def _answers(payload: dict) -> dict:
    """Nest exposes answers at data.result.answers. OpenRouter also returns top-level answers."""
    data = payload.get("data")
    if isinstance(data, dict):
        result = data.get("result")
        if isinstance(result, dict) and isinstance(result.get("answers"), dict):
            return result["answers"]
    answers = payload.get("answers")
    return answers if isinstance(answers, dict) else {}


def _distributions(payload) -> dict:
    if not isinstance(payload, dict):
        return {}
    out = {}
    for name, answer in _answers(payload).items():
        dist = _probability_map(answer)
        if dist:
            out[str(name)] = dist
    return out


def _post(url: str, headers: dict, body: dict, timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"jev HTTP {exc.code}") from None
    if not isinstance(payload, dict):
        raise RuntimeError("jev response was not an object")
    return payload


class OpenRouterJev:
    """Live classifier. Same classify() contract as MockJev.

    Sends only the customer text and the questions. `facts` are not uploaded.
    One failed batch contributes nothing; other batches are kept. No retries.
    """

    def __init__(self, post=None):
        self._post = post or _post

    def classify(self, text: str, qs: list[dict], facts: list[AttributeFact]) -> dict:
        del facts  # interface matches MockJev; the request must not carry step A facts
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not key:
            return {}
        model = os.getenv("JEV_MODEL", "").strip() or JEV_DEFAULT_MODEL
        out: dict = {}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        for batch in _batches(qs, JEV_BATCH):
            questions = _choice_questions(batch)
            if not questions:
                continue
            body = {"model": model, "state": text, "questions": questions}
            try:
                payload = self._post(JEV_URL, headers, body, JEV_TIMEOUT_S)
            except Exception:
                continue
            out.update(_distributions(payload))
        return out


class MockJev:
    """Deterministic stand-in: echoes known attributes with high p, says not_stated for the rest.
    `overrides` = {attribute: {option: p}} to simulate disagreements in tests and demos."""

    def __init__(self, overrides: dict | None = None, p_known: float = 0.9):
        self.overrides = overrides or {}
        self.p_known = p_known

    def classify(self, text: str, qs: list[dict], facts: list[AttributeFact]) -> dict:
        by = {f.name: f for f in facts}
        out = {}
        for q in qs:
            name = q["id"]
            if name in self.overrides:
                out[name] = dict(self.overrides[name])
                continue
            f = by.get(name)
            if f is not None and f.status == "known" and f.value in q["options"]:
                rest = (1 - self.p_known) / max(1, len(q["options"]) - 1)
                out[name] = {o: (self.p_known if o == f.value else rest) for o in q["options"]}
            else:
                out[name] = {NOT_STATED: 0.7, **{o: 0.3 / max(1, len(q["options"]) - 1)
                                                for o in q["options"] if o != NOT_STATED}}
        return out


def selftest() -> None:
    qs = questions()
    assert len(qs) == len(vocabulary()) and all(q["options"][-1] == NOT_STATED for q in qs)
    facts = [
        AttributeFact(name="sample_form", value="liquid", status="known", quote="petroleum line"),
        AttributeFact(name="matrix_aqueous", value="yes", status="assumed", quote=None),
        AttributeFact(name="optical_density", value=None, status="unknown", quote=None),
        AttributeFact(name="distance", value="other_building", status="known", quote="another building"),
    ]
    jev = MockJev(overrides={
        "matrix_aqueous": {"no": 0.8, "yes": 0.1, NOT_STATED: 0.1},          # assumption contradicted
        "optical_density": {"opaque": 0.75, "clear": 0.05, "turbid": 0.1, "varies": 0.05, NOT_STATED: 0.05},
        "distance": {"at_process": 0.7, "other_building": 0.2, NOT_STATED: 0.1},  # quote vs Jev
    })
    dists = jev.classify("…", qs, facts)
    merged, votes, notes = merge(facts, dists)
    by = {f.name: f for f in merged}
    assert by["sample_form"].status == "known"
    assert by["matrix_aqueous"].status == "unknown"            # becomes a question
    assert by["optical_density"].status == "unknown"           # Jev never fills a gap
    assert by["distance"].status == "conflicting"              # quote and Jev disagree -> expert
    assert any(v.name == "sample_form" and v.agrees for v in votes)
    w = distributions_for_voi(dists)["optical_density"]
    assert abs(sum(w.values()) - 1) < 1e-9 and NOT_STATED not in w
    print(f"jev OK: {len(qs)} questions, {len(votes)} votes, {len(notes)} notes")
    for n in notes:
        print("   ", n)


if __name__ == "__main__":
    selftest()
