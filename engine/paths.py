"""Decision path ("why this method"): the trace of engine.gates as a tree Q1 -> Q2 -> Q3 -> Q4 -> decision.

    python -m engine.paths            # writes docs/decision-paths.md (Mermaid, renders on GitHub)
                                      # and eval/paths/<case>.json (for the screen)
    path_json(attrs)  -> dict         # one case, for the frontend
    mermaid(attrs)    -> str          # one case, for slides / README

Only the steps that explain the decision are shown: exclusions, premise verdicts, case status, AFS
application evidence, and needs_info / high risks on the rows that matter. Everything else is counted.
Input here = the golden attributes (written by hand), not a live extraction.
"""
import json
from pathlib import Path

from .gates import assess
from .gates_loader import load_gates, load_yaml

ROOT = Path(__file__).resolve().parents[1]
STEP_TITLE = {"Q1": "Q1 Task", "Q2": "Q2 Signal", "Q3": "Q3 Interface and fiber", "Q4": "Q4 Premises and evidence"}
KEY_EFFECTS = {"exclude", "exclude_config", "premise_contradicted", "premise_not_supported",
               "case_insufficient", "case_outside_scope", "split_case", "cap_provisional", "support_application"}


def path_json(attrs: dict, g: dict | None = None) -> dict:
    g = g or load_gates()
    a = assess(attrs, g=g)
    rules = {r["id"]: r for r in g["rules"]}
    rows = {r.row: r for r in a.rows}
    focus = set(a.selected) | {r.row for r in a.rows if r.evidence == "application"}
    steps = {s: {"title": t, "shown": [], "hidden": 0} for s, t in STEP_TITLE.items()}
    seen = set()
    for t in a.trace:
        key = (t.rule_id, t.target, t.effect)
        if key in seen:
            continue
        seen.add(key)
        important = t.effect in KEY_EFFECTS or (t.target in focus and t.effect in {"needs_info", "risk_high", "support_physics", "fit"})
        if t.step not in steps:
            continue
        if important:
            cat = g["catalog"].get(t.target, {}) if t.target else {}
            steps[t.step]["shown"].append({
                "rule_id": t.rule_id, "row": t.target,
                "row_label": f"{cat.get('method', '').upper()} {cat.get('technique', '')}".strip() if t.target else None,
                "effect": t.effect, "because": rules[t.rule_id]["because"], "source": t.source})
        else:
            steps[t.step]["hidden"] += 1
    label = lambda rid: f"{rid} {g['catalog'][rid]['method'].upper()} {g['catalog'][rid]['technique']}"
    return {
        "decision_status": a.decision_status,
        "selected": [label(r) for r in a.selected],
        "excluded": [label(r.row) for r in a.rows if r.status == "excluded"],
        "premises": [{"rule_id": p.rule_id, "verdict": p.verdict, "text": p.text, "source": p.source}
                     for p in a.premise_flags],
        "steps": list(steps.values()),
        "questions": [{"attribute": q.attribute, "kind": q.kind, "strength": q.strength, "forced": q.forced,
                       "text": q.text} for q in a.questions],
        "lab_checks": [q.text for q in a.lab_checks],
        "evidence": {r: rows[r].evidence for r in a.selected},
    }


def _esc(s: str) -> str:
    return s.replace('"', "'").replace("<", "‹").replace(">", "›")


def mermaid(attrs: dict, g: dict | None = None) -> str:
    p = path_json(attrs, g)
    lines = ["flowchart TD"]
    prev = None
    for i, st in enumerate(p["steps"]):
        items = [f"{s['rule_id']}{' · ' + s['row'] if s['row'] else ''}: {s['effect']}" for s in st["shown"][:6]]
        if len(st["shown"]) > 6:
            items.append(f"+{len(st['shown']) - 6} more")
        if st["hidden"]:
            items.append(f"({st['hidden']} minor effects)")
        body = "<br/>".join(_esc(x) for x in items) or "no decisive rule"
        lines.append(f'  S{i}["<b>{_esc(st["title"])}</b><br/>{body}"]')
        if prev is not None:
            lines.append(f"  S{prev} --> S{i}")
        prev = i
    sel = "<br/>".join(_esc(x) for x in p["selected"]) or "no method can be justified yet"
    lines.append(f'  D["<b>{p["decision_status"]}</b><br/>{sel}"]')
    lines.append(f"  S{prev} --> D")
    qs = [q for q in p["questions"] if q["kind"] == "method"][:3]
    if qs:
        qtext = "<br/>".join(_esc(f"{q['attribute']} ({'forced' if q['forced'] else q['strength']})") for q in qs)
        lines.append(f'  Q["<b>Ask first</b><br/>{qtext}"]')
        lines.append("  D -.-> Q")
    return "\n".join(lines)


def _golden_units():
    cases = load_yaml(ROOT / "eval" / "golden_cases.yaml")["cases"]
    for cid, c in cases.items():
        if c.get("subcases"):
            for sid, s in c["subcases"].items():
                yield sid, c.get("title", ""), {**c["attrs"], **s.get("attrs", {})}
        else:
            yield cid, c.get("title", ""), c["attrs"]


def main() -> None:
    g = load_gates()
    out_dir = ROOT / "eval" / "paths"
    out_dir.mkdir(parents=True, exist_ok=True)
    md = ["# Decision paths (why this method)", "",
          "Generated by `python -m engine.paths` from `rules/gates.yaml` on the golden attributes",
          "(`eval/golden_cases.yaml`, written by hand, not a live extraction). D01-D08 = development,",
          "H01-H06 = test. Each box lists the rules that decided the step; minor effects are only counted.", ""]
    for uid, title, attrs in _golden_units():
        (out_dir / f"{uid}.json").write_text(json.dumps(path_json(attrs, g), ensure_ascii=False, indent=2),
                                             encoding="utf-8")
        md += [f"## {uid} · {title}", "", "```mermaid", mermaid(attrs, g), "```", ""]
    (ROOT / "docs" / "decision-paths.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote docs/decision-paths.md and {len(list(out_dir.glob('*.json')))} files in eval/paths/")


if __name__ == "__main__":
    main()
