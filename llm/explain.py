"""Step B: engine result -> rationale, questions, experiment, risks.  C6 -> C7.

v0.3: when C6.scoring.assessment (gates engine) is present, step B also gets a compact, readable
view of it (decision status, premise verdicts, engine questions, lab checks, the AFS sources behind
each method). After the call, `_check` removes what step B is not allowed to invent:
claims with neither a provided knowledge card nor a source from the engine trace, sources that are
not in the trace, question attributes outside the vocabulary, rationale for methods that were not ranked.
"""
import json
import os
import re

from contracts.models import ExplainInput, Explanation

from .client import MODEL_REASON, ROOT, example, is_mock, parse, prompt
from .vocab import ATTR_TO_PARAM, vocabulary

KB = ROOT / "kb"
AFS_SOURCE_CARD = "afs-source"   # kb_card value for a claim that rests on an AFS source from the engine trace
_SHOWN_EFFECTS = {"exclude", "exclude_config", "support_application", "support_physics", "risk_high",
                  "premise_contradicted", "premise_not_supported", "case_insufficient", "case_outside_scope",
                  "split_case", "clarify", "cap_provisional"}


def _card_files(methods: list[str]):
    files = []
    for m in methods:
        f = KB / f"card-{m.replace('_', '-')}.md"
        if f.exists():
            files.append(f)
    files += sorted(KB.glob("expert-*.md"))
    return files


def _cards(methods: list[str]) -> str:
    return "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in _card_files(methods))


def _card_ids(methods: list[str]) -> set[str]:
    return {f.stem for f in _card_files(methods)}


def _gates_view(inp: ExplainInput) -> tuple[str, set[str]]:
    """Readable summary of C5.assessment for step B, and the set of AFS sources it may cite."""
    a = inp.scoring.assessment
    if a is None:
        return "", set()
    from engine.gates_loader import load_gates   # lazy: only needed when an assessment is present
    g = load_gates()
    because = {r["id"]: r.get("because", "") for r in g["rules"]}
    cat = g["catalog"]
    label = lambda rid: f"{rid} {cat[rid]['method'].upper()} {cat[rid]['technique']}" if rid in cat else rid
    sources: set[str] = set()
    per_row: dict[str, list[str]] = {}
    case_lines: list[str] = []
    seen = set()
    for t in a.trace:
        shown = t.effect in _SHOWN_EFFECTS or (t.target is None and t.effect == "risk")   # case-level risks too
        if not shown or (t.rule_id, t.target, t.effect) in seen:
            continue
        seen.add((t.rule_id, t.target, t.effect))
        sources.update(t.source)
        line = f"{t.effect} · {t.rule_id}: {because.get(t.rule_id, '')} [sources: {'; '.join(t.source) or 'none'}]"
        (per_row.setdefault(t.target, []) if t.target else case_lines).append(line)
    for p in a.premise_flags:
        sources.update(p.source)
    view = {
        "decision_status": a.decision_status,
        "selected_rows_best_first": [label(r) for r in a.selected],
        "rows": {label(r.row): {"status": r.status, "evidence": r.evidence, "risks": r.risks,
                                "rules": per_row.get(r.row, [])}
                 for r in a.rows if r.status != "excluded" or per_row.get(r.row)},
        "case_rules": case_lines,
        "premise_verdicts": [{"rule_id": p.rule_id, "verdict": p.verdict, "text": p.text, "sources": p.source}
                             for p in a.premise_flags],
        "combinations": a.combinations,
        "questions_from_engine": [{"attribute": q.attribute, "kind": q.kind, "forced": q.forced,
                                   "strength": q.strength, "text": q.text,
                                   "parameter_id": ATTR_TO_PARAM.get(q.attribute)} for q in a.questions],
        "lab_checks_step0": [q.text for q in a.lab_checks],
    }
    return json.dumps(view, ensure_ascii=False, indent=1), sources


B_RUBRIC = (
    "Method B rubric (spec spectroscopy-rules 1.2, design_v0_unvalidated): each candidate = method x interface x "
    "configuration concept. Q1 = signal and separability of the target (observability, distinguishability); "
    "Q1b = achievability of concentration/error/speed (UNKNOWN when the AFS materials give no profile); "
    "Q2 = optical access of this interface to this sample; Q3 = process compatibility of the configuration. "
    "Each 0-9, higher = more supporting factors: 8-9 strong, 5-7 good/acceptable, 2-4 weak/doubtful, 0-1 critical; "
    "a score is never a probability and 0 is not an exclusion. suitability = Q1+Q1b+Q2+Q3 (0-36) with an interval "
    "over the unknowns. Q4 (0-3) = strength and closeness of the evidence, used only for confidence. "
    "critical_unknown = an unknown fact whose value could change the leading method: keep the recommendation "
    "conditional and ask that question first. Fact status: reported (client said it), inferred, unknown "
    "(unresolved, never false), confirmed_experiment / confirmed_expert, conflicting."
)


def engine_controls() -> str:
    """Which engine's result step B explains: ENGINE=b -> method B, otherwise method A (gates)."""
    return "b" if os.environ.get("ENGINE", "ab").lower() == "b" else "a"


def _b_view(inp: ExplainInput) -> tuple[str, set[str]]:
    """Compact, readable view of C5.assessment_b for step B (the raw JSON is ~130 kB) and its citable sources."""
    b = getattr(inp.scoring, "assessment_b", None)
    if not b:
        return "", set()
    sources: set[str] = set()
    cases = []
    for co in b.get("cases", []):
        top = []
        for c in co.get("ranking", [])[:3]:
            reasons = []
            for f in c.get("factor_contributions", []):
                if f.get("outcome") in ("MATCH", "MISMATCH") and f.get("selected_in_exclusive_group") and f.get("effect"):
                    for x in (f.get("source") or "").split(";"):
                        if x.strip():
                            sources.add(x.strip())
                    reasons.append(f"{f['stage']} {f['outcome']} {f['effect']:+d}: {f.get('note') or ''} "
                                   f"[source: {f.get('source') or 'none'}]")
            top.append({"candidate": f"{c['method_id']} / {c['interface_name']} / link {c['configuration']['link']}",
                        "scores": {q: c["question_results"][q]["display_score"] for q in ("Q1", "Q1b", "Q2", "Q3")},
                        "suitability": c["suitability"], "interval": c["suitability_interval"],
                        "q4": c["q4_score"], "confidence": c["confidence"], "critical_unknown": c["critical_unknown"],
                        "deployment_status": c["deployment_status"], "reasons": reasons})
        cases.append({"case": co["case_id"], "status": co["decision_status"], "headline": co.get("headline"),
                      "methods_best_first": [f"{m['method_id']} {m['suitability']}/36 interval {m['suitability_interval']}"
                                             for m in co.get("methods", [])],
                      "top_candidates": top,
                      "questions": [{"priority": q["priority"], "text": q["text"], "why": q["why"]}
                                    for q in co.get("questions", [])],
                      "first_experiment": co.get("first_experiment"),
                      "combinations": [{"methods": cb["methods"], "hypothesis": cb["hypothesis_of_gain"],
                                        "source": cb["source"]} for cb in co.get("combinations", [])]})
    for p in b.get("premises", []):
        for x in (p.get("source") or "").split(";"):
            if x.strip():
                sources.add(x.strip())
    facts = b.get("facts", {})
    view = {"rubric": B_RUBRIC, "cases": cases, "aggregate_bundle": b.get("aggregate_bundle"),
            "premises": b.get("premises", []),
            "facts_reported": {k: v["value"] for k, v in facts.items() if v.get("status") == "reported"},
            "facts_inferred": {k: v["value"] for k, v in facts.items() if v.get("status") == "inferred"},
            "facts_unknown": sorted(k for k, v in facts.items() if v.get("status") == "unknown")}
    return json.dumps(view, ensure_ascii=False, indent=1), sources


def _src_key(s: str) -> str:
    """'S01 p. 10' and 'S01 p.10' and 'S01 p.10–11' vs 'S01 p.10-11' are the same source."""
    return re.sub(r"\s+", "", s.replace("\u2013", "-").replace("\u2014", "-")).casefold()


def _check(ex: Explanation, inp: ExplainInput, cards: set[str], sources: set[str]) -> Explanation:
    """Remove what step B may not invent. Logs every removal."""
    ranked = {r.method for r in inp.scoring.ranked}
    by_key = {_src_key(x): x for x in sources}
    vocab = set(vocabulary())
    rationale = []
    for r in ex.rationale:
        if r.method not in ranked:
            print(f"[llm] B/check: rationale for unranked method {r.method} dropped")
            continue
        claims = []
        for c in r.claims:
            src = by_key.get(_src_key(c.source)) if c.source else None   # canonical spelling from the trace
            if c.source and src is None:
                print(f"[llm] B/check: source {c.source!r} not in the engine trace -> removed")
            if c.kb_card in cards:
                claims.append(c.model_copy(update={"source": src}))
            elif src:
                claims.append(c.model_copy(update={"kb_card": AFS_SOURCE_CARD, "source": src}))
            else:
                print(f"[llm] B/check: claim without a provided card or trace source dropped ({c.kb_card})")
        rationale.append(r.model_copy(update={"claims": claims}))
    questions = []
    for q in ex.questions:
        if q.attribute is not None and q.attribute not in vocab:
            print(f"[llm] B/check: question {q.id} attribute {q.attribute!r} not in the vocabulary -> null")
            q = q.model_copy(update={"attribute": None})
        questions.append(q)
    return ex.model_copy(update={"rationale": rationale, "questions": questions})


def explain(inp: ExplainInput) -> Explanation:
    if is_mock():
        return Explanation.model_validate(example("C7_explanation.example.json"))
    methods = [r.method for r in inp.scoring.ranked] + [r.method for r in inp.scoring.rejected]
    mode = engine_controls()
    gates, sources = _gates_view(inp)
    bview, bsources = _b_view(inp) if mode == "b" else ("", set())
    sources |= bsources
    case = inp.model_dump(mode="json")
    case["scoring"].pop("assessment", None)          # shown in readable form below instead of raw JSON
    case["scoring"].pop("assessment_b", None)        # ~130 kB raw; method B is shown in readable form when it controls
    if mode == "b":
        assessment = f"\n\n<method_b_assessment>\n{bview}\n</method_b_assessment>" if bview else ""
    else:
        assessment = f"\n\n<gates_assessment>\n{gates}\n</gates_assessment>" if gates else ""
    user = (
        f"Case language: {inp.language}\n\n<knowledge_cards>\n{_cards(methods)}\n</knowledge_cards>\n\n"
        f"<case>\n{json.dumps(case, ensure_ascii=False, indent=1)}\n</case>" + assessment
    )
    system = prompt("explain_system.md")
    if mode == "b" and os.environ.get("EXPLAIN_REASONING", "1").lower() in ("1", "true", "yes"):
        # domain-reasoning addendum (spectrascout-reasoning 1.2.0, core only); the host prompt stays authoritative
        system += "\n\n" + prompt("explain_reasoning_supplement.md") + "\n\nCaller-selected assessment mode: method B."
    ex = parse(system, user, Explanation, max_tokens=9000, step="B/explain", model=MODEL_REASON)
    return _check(ex, inp, _card_ids(methods), sources)
