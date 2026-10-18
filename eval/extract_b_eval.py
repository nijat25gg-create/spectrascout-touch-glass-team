"""Step A for method B against eval/golden_b.yaml, plus the engine-B leader on the extracted facts.

    python -m eval.extract_b_eval --live            # real Claude calls (key in .env), D01-D08
    python -m eval.extract_b_eval --live --with-h   # also H01-H06 (frozen: measure only, never tune on them)

Writes eval/extract_b_report_live.md. No customer text or quote goes into the report (AFS copyright).
Per case: golden keys matched / wrong / missed, extra facts step A filled that golden leaves unknown (to review),
and whether the leading method on the extracted facts is one the golden expects.
"""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _norm(v):
    if v is None:
        return None
    return sorted(v) if isinstance(v, list) else str(v)


def compare(golden: dict, facts: dict) -> dict:
    got = {k: _norm(r["value"]) for k, r in facts.items() if r.get("status") not in ("unknown", "conflicting")}
    ok, wrong, missed, status = [], [], [], []
    for k, g in golden.items():
        # golden fact: plain value (reported) or {value, status, quote/source}
        gv, gs = (g.get("value"), g.get("status", "reported")) if isinstance(g, dict) else (g, "reported")
        gv = _norm(gv)
        if k not in got:
            missed.append(k)
        elif got[k] == gv:
            ok.append(k)
            if facts[k]["status"] != gs:
                status.append(f"{k}: got {facts[k]['status']}, golden {gs}")
        else:
            wrong.append(f"{k}: got {got[k]}, golden {gv}")
    extra = sorted(f"{k}={got[k]} ({facts[k]['status']})" for k in got if k not in golden)
    return {"ok": ok, "wrong": wrong, "missed": missed, "extra": extra, "status": status}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="call Claude (needs the key in .env)")
    ap.add_argument("--with-h", action="store_true", help="also measure H01-H06 (frozen)")
    args = ap.parse_args()
    if not args.live:
        ap.error("only --live is meaningful: the mock returns one canned extraction for every case")
    from llm.client import is_mock   # importing loads .env, which may switch the mock on
    if is_mock():
        ap.error("LLM_MOCK is on (shell or .env): run with LLM_MOCK=0 for --live")
    os.environ.setdefault("EXTRACT_B", "1")

    from contracts.models import ExtractInput
    from engine.b import assess_b
    from eval.case_texts import load_case_texts
    from llm.extract import extract
    from llm.facts_b import to_engine

    gold = yaml.safe_load((ROOT / "eval/golden_b.yaml").read_text(encoding="utf-8"))["cases"]
    texts = load_case_texts()
    ids = [c for c in sorted(gold) if c.startswith("D") or (args.with_h and c.startswith("H"))]
    lines = ["# Step A (method B facts) vs eval/golden_b.yaml, live", "",
             "| case | golden keys ok | wrong | missed | extra (review) | leader | expected | s |", "|---|---|---|---|---|---|---|---|"]
    details = []
    tot_ok = tot_all = lead_ok = lead_n = 0
    for cid in ids:
        t0 = time.time()
        ex = extract(ExtractInput(case_id=cid, text=texts[cid], language="en"))
        facts = to_engine(ex.facts_b)
        res = assess_b(facts)
        rec = res["facts"]
        cmp = compare(gold[cid]["facts"], rec)
        leaders = [co["methods"][0]["method_id"] for co in res["cases"] if co["methods"]]
        exp = gold[cid].get("expect", {}).get("leader_methods")
        good = (all(l in exp for l in leaders) if exp and leaders else None)
        n = len(gold[cid]["facts"])
        tot_ok += len(cmp["ok"]); tot_all += n
        if good is not None:
            lead_n += 1; lead_ok += int(good)
        lines.append(f"| {cid} | {len(cmp['ok'])}/{n} | {len(cmp['wrong'])} | {len(cmp['missed'])} | {len(cmp['extra'])} | "
                     f"{', '.join(leaders) or res['cases'][0]['decision_status']} | {', '.join(exp or []) or '-'} | {time.time() - t0:.0f} |")
        details += [f"## {cid}", f"- headline: {res['cases'][0]['headline']}",
                    *[f"- wrong: {w}" for w in cmp["wrong"]], *[f"- missed: {m}" for m in cmp["missed"]],
                    *[f"- status: {e}" for e in cmp["status"]], *[f"- extra: {e}" for e in cmp["extra"]], ""]
        print(cid, f"{len(cmp['ok'])}/{n}", leaders, flush=True)
    lines += ["", f"**Golden facts matched: {tot_ok}/{tot_all}. Leader as expected: {lead_ok}/{lead_n}.**", ""] + details
    out = ROOT / "eval/extract_b_report_live.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: facts {tot_ok}/{tot_all}, leader {lead_ok}/{lead_n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
