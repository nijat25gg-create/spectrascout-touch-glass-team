"""Step-A accuracy and end-to-end check: customer text -> attributes -> engine.gates, against golden.

    python eval/extract_eval.py --live                # real llm.extract (needs the API key in .env)
    python eval/extract_eval.py --from-dir DIR        # pre-computed outputs: DIR/<case>.json = {"attributes": [...]}
    python eval/extract_eval.py --synthetic --from-dir DIR   # S01-S04 from eval/synthetic_cases.yaml (own texts)
    options: --cases D01,D02   --out eval/extract_report.md

D01-D08 = development (tune on these), H01-H06 = test (report only; never tune prompt or rules on H).
Golden attributes are hand-written expectations (eval/golden_cases.yaml), not AFS answers.

Per attribute:
  match    our value == golden value
  wrong    both set, values differ
  missed   golden set, ours unknown
  extra    golden unknown (not listed), ours known/assumed -> either an invention or a gap in golden; review
Quotes: every known value must quote the customer text verbatim (normalisation enforces it; counted here).
End to end: engine.gates on our attributes vs golden expect (status, top_include, must_exclude, premises).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.models import AttributeFact, ExtractInput  # noqa: E402
from engine.gates import assess  # noqa: E402
from engine.gates_loader import load_yaml  # noqa: E402
from eval.case_texts import load_case_texts  # noqa: E402
from llm.vocab import engine_attrs, normalize_attributes  # noqa: E402

GOLDEN = load_yaml(ROOT / "eval" / "golden_cases.yaml")["cases"]
SYNTHETIC = load_yaml(ROOT / "eval" / "synthetic_cases.yaml")["cases"]


def _facts_from_dir(d: Path, cid: str) -> list:
    raw = json.loads((d / f"{cid}.json").read_text(encoding="utf-8"))
    facts = []
    for a in raw.get("attributes", []):
        try:
            facts.append(AttributeFact.model_validate(a))
        except Exception as e:  # noqa: BLE001  an invalid entry counts as missing, and is reported
            print(f"[{cid}] invalid attribute entry dropped: {a!r} ({str(e).splitlines()[0]})")
    return facts


def _facts_live(cid: str, text: str, language: str = "en") -> list:
    from llm.extract import extract
    c3 = extract(ExtractInput(case_id=cid, text=text, language=language))
    return c3.attributes or []


def _golden_attr_options(case: dict) -> dict:
    """{name: set(values)}: parent attrs, plus every subcase value (one extraction covers all subcases)."""
    opts = {k: {str(v)} for k, v in case.get("attrs", {}).items()}
    for sub in (case.get("subcases") or {}).values():
        for k, v in (sub.get("attrs") or {}).items():
            opts.setdefault(k, set()).add(str(v))
    return opts


def _expect_units(case: dict, ours: dict):
    """Pick the golden unit to compare the engine with: the subcase whose attrs agree most with ours."""
    subs = case.get("subcases") or {}
    if not subs:
        return case.get("expect", {}), case.get("attrs", {})
    best = max(subs.items(), key=lambda kv: sum(ours.get(k) == str(v) for k, v in (kv[1].get("attrs") or {}).items()))
    exp = {**case.get("expect", {}), **(best[1].get("expect") or {})}
    return exp, {**case["attrs"], **(best[1].get("attrs") or {})}


def evaluate(cid: str, facts: list, text: str) -> dict:
    facts, notes = normalize_attributes(facts, text)
    ours = engine_attrs(facts)
    status_of = {f.name: f.status for f in facts}
    gold_case = GOLDEN.get(cid) or SYNTHETIC[cid]
    gold = _golden_attr_options(gold_case)
    res = {"case": cid, "match": [], "wrong": [], "missed": [], "extra": [], "notes": notes}
    for name, values in gold.items():
        v = ours.get(name)
        if v is None:
            res["missed"].append(name)
        elif v in values:
            res["match"].append(name)
        else:
            res["wrong"].append(f"{name}: ours {v} vs golden {'/'.join(sorted(values))}")
    for name, v in ours.items():
        if name not in gold:
            res["extra"].append(f"{name}={v} ({status_of[name]})")
    exp, _ = _expect_units(gold_case, ours)
    a = assess(ours)
    e2e = []
    if exp.get("status") and a.decision_status != exp["status"]:
        e2e.append(f"status {a.decision_status} vs {exp['status']}")
    for row in exp.get("top_include", []):
        if row not in a.selected:
            e2e.append(f"{row} not in top {a.selected}")
    if exp.get("top1") and a.selected[:1] != [exp["top1"]]:
        e2e.append(f"top-1 {a.selected[:1]} vs {exp['top1']}")
    rows = {r.row: r for r in a.rows}
    for row in exp.get("must_exclude", []):
        if rows[row].status != "excluded":
            e2e.append(f"{row} should be excluded ({rows[row].status})")
    flags = {p.rule_id: p.verdict for p in a.premise_flags}
    for rid, verdict in (exp.get("premises") or {}).items():
        if flags.get(rid) != verdict:
            e2e.append(f"premise {rid} {flags.get(rid)} vs {verdict}")
    res.update(e2e=e2e, status=a.decision_status, selected=a.selected,
               questions=[q.attribute for q in a.questions if q.kind == "method"])
    return res


def report(results: list, source: str) -> str:
    def block(title, rs):
        if not rs:
            return []
        n_g = sum(len(r["match"]) + len(r["wrong"]) + len(r["missed"]) for r in rs)
        n_m = sum(len(r["match"]) for r in rs)
        n_w = sum(len(r["wrong"]) for r in rs)
        n_x = sum(len(r["extra"]) for r in rs)
        n_ok = sum(1 for r in rs if not r["e2e"])
        out = [f"## {title}", "",
               f"Attributes: **{n_m}/{n_g} match** ({n_m / max(1, n_g):.0%}), {n_w} wrong, "
               f"{n_g - n_m - n_w} missed, {n_x} extra (review: invention or gap in golden).",
               f"End to end (engine on our attributes vs golden expect): **{n_ok}/{len(rs)} cases without deviation**.", "",
               "| Case | match | wrong | missed | extra | engine status · top | deviations |", "|---|---|---|---|---|---|---|"]
        for r in rs:
            out.append(f"| {r['case']} | {len(r['match'])} | {'; '.join(r['wrong']) or '–'} | {', '.join(r['missed']) or '–'} "
                       f"| {', '.join(r['extra']) or '–'} | {r['status']} · {', '.join(r['selected']) or '–'} "
                       f"| {'; '.join(r['e2e']) or 'ok'} |")
        return out + [""]
    d = [r for r in results if r["case"].startswith("D")]
    h = [r for r in results if r["case"].startswith("H")]
    syn = [r for r in results if r["case"].startswith("S")]
    lines = ["# Step-A extraction evaluation", "", f"Source of attributes: {source}.",
             "Golden = hand-written expectations (eval/golden_cases.yaml). D = development, H = test (report only).", ""]
    lines += block("DEV D01–D08", d) + block("TEST H01–H06 (report only, no tuning)", h)
    lines += block("SYNTHETIC S01–S04 (own texts, written without AFS materials; generalisation check)", syn)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--live", action="store_true")
    g.add_argument("--from-dir")
    ap.add_argument("--synthetic", action="store_true", help="use eval/synthetic_cases.yaml instead of D/H")
    ap.add_argument("--cases", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--source", default="")
    args = ap.parse_args()
    from llm.client import is_mock   # importing loads .env, which may switch the mock on
    if args.live and is_mock():
        ap.error("--live with LLM_MOCK on (shell or .env) would score the canned example for every case; "
                 "run with LLM_MOCK=0")
    if not args.out:
        args.out = str(ROOT / "eval" / ("extract_report_synthetic.md" if args.synthetic else "extract_report.md"))
    texts = ({k: v["text"] for k, v in SYNTHETIC.items()} if args.synthetic else load_case_texts())
    cases = [c for c in (args.cases.split(",") if args.cases else sorted(texts)) if c]
    results = []
    for cid in cases:
        lang = SYNTHETIC[cid]["language"] if cid in SYNTHETIC else "en"
        facts = _facts_live(cid, texts[cid], lang) if args.live else _facts_from_dir(Path(args.from_dir), cid)
        results.append(evaluate(cid, facts, texts[cid]))
    src = args.source or ("live llm.extract" if args.live else f"files in {args.from_dir}")
    md = report(results, src)
    Path(args.out).write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
