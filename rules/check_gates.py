"""Check rules/gates.yaml and run the golden cases with a small reference evaluator.

    python rules/check_gates.py            # validate + golden
    python rules/check_gates.py --case H04 # show the full trace of one case

Part 1 (structure): unique ids, known step/applies_to/effect, every input attribute declared with a
finite value list containing "unknown", sources present, tests or an `untested` reason, test ids exist.
Part 2 (golden): engine/gates.py (the engine itself) runs eval/golden_cases.yaml and `expect` is checked.
Deterministic, no LLM call.
Exit code 1 if anything fails.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "rules" / "gates.yaml"
GOLDEN = ROOT / "eval" / "golden_cases.yaml"

STEPS = {"Q1", "Q2", "Q3", "Q4", "OUT"}
APPLIES = {"case", "method", "row", "combination"}
ON_UNKNOWN = {"ignore", "needs_info", "plan_question", "case_insufficient", "risk"}
PREMISES = {"contradicted", "not_supported"}

# The engine module itself is the single implementation of the semantics. It is loaded as a plain
# module (engine/ on the path) so this check runs without pydantic or the rest of the engine package.
sys.path.insert(0, str(ROOT / "engine"))
from gates import EVID_RANK, Evaluator, overlap  # noqa: E402
from gates_loader import load_yaml as load  # noqa: E402  yes/no stay strings


errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


# ------------------------------------------------------------------ part 1: structure
def validate(g: dict, golden: dict) -> None:
    attrs, computed = g["attributes"], g.get("computed", {})
    methods, rows = set(g["methods"]), set(g["catalog"])
    effects = set(g["effects"])
    for name, a in attrs.items():
        vals = a.get("values") or []
        if "unknown" not in vals:
            err(f"attribute {name}: value list must contain 'unknown' (needed for enumeration)")
        if len(vals) > 15:
            warnings.append(f"attribute {name}: {len(vals)} values, enumeration gets expensive")
    for rid, r in g["catalog"].items():
        if r["method"] not in methods:
            err(f"catalog {rid}: unknown method {r['method']}")
        if r["cost"] not in g["cost_order"]:
            err(f"catalog {rid}: cost {r['cost']} not in cost_order")
        # sample types must be sample_form values; K09 'radiating_sample' (emission) is a documented exception
        for st in r.get("sample_types", []):
            if st not in [str(v) for v in attrs["sample_form"]["values"]] and st != "radiating_sample":
                err(f"catalog {rid}: sample type {st!r} is not a sample_form value")
    fo = g.get("fiber_full_overlap", 1.0)
    for k, v in (fo.items() if isinstance(fo, dict) else [("default", fo)]):
        if k != "default" and k not in methods:
            err(f"fiber_full_overlap: unknown method {k}")
        if not isinstance(v, (int, float)) or not 0 < v <= 1:
            err(f"fiber_full_overlap.{k}: must be a number in (0, 1], got {v!r}")
    qs = g.get("questions", {})
    for name in attrs:
        q = qs.get(name)
        if q is None:
            err(f"attribute {name}: no entry in questions:")
        elif q.get("kind") not in {"method", "plan", "lab_check", "never"}:
            err(f"questions.{name}: kind must be method|plan|lab_check|never")
        elif q["kind"] != "never" and not q.get("text"):
            err(f"questions.{name}: no text")
    for tb in g.get("tie_break", []):
        if tb.get("column") not in {"sensitivity", "selectivity", "cost"}:
            err(f"tie_break: unknown column {tb.get('column')}")
        if not tb.get("source"):
            err("tie_break: entry without source")
        for k, vals in (tb.get("when") or {}).items():
            if k not in attrs:
                err(f"tie_break: undeclared attribute {k}")
    golden_ids = set(golden["cases"])
    seen = set()
    for r in g["rules"]:
        rid = r.get("id", "?")
        if rid in seen:
            err(f"{rid}: duplicate id")
        seen.add(rid)
        if rid != rid.upper():
            err(f"{rid}: id must be UPPER-CASE")
        for f in ("step", "applies_to", "targets", "when", "effect", "on_unknown", "because", "source", "tests"):
            if f not in r:
                err(f"{rid}: missing field {f}")
        if r.get("step") not in STEPS:
            err(f"{rid}: bad step {r.get('step')}")
        if r.get("applies_to") not in APPLIES:
            err(f"{rid}: bad applies_to {r.get('applies_to')}")
        if r.get("effect") not in effects:
            err(f"{rid}: unknown effect {r.get('effect')}")
        if r.get("on_unknown") not in ON_UNKNOWN:
            err(f"{rid}: bad on_unknown {r.get('on_unknown')}")
        for t in r.get("targets") or []:
            if t not in methods and t not in rows:
                err(f"{rid}: unknown target {t}")
        if r.get("applies_to") in {"method", "row"} and r.get("step") != "OUT" and not r.get("targets"):
            err(f"{rid}: {r['applies_to']} rule without targets")
        if r.get("step") != "OUT":
            if r.get("applies_to") == "method" and any(t not in methods for t in r.get("targets") or []):
                err(f"{rid}: method rule must target methods, got {r.get('targets')}")
            if r.get("applies_to") == "row" and any(t not in rows for t in r.get("targets") or []):
                err(f"{rid}: row rule must target catalog rows, got {r.get('targets')}")
            if r.get("applies_to") == "combination":
                err(f"{rid}: applies_to combination is only allowed for OUT rules")
        for k in (r.get("guard") or {}):
            if k not in attrs:
                err(f"{rid}: guard may only use plain attributes, not {k}")
        if r.get("premise") is not None and r.get("premise") not in PREMISES:
            err(f"{rid}: premise must be one of {sorted(PREMISES)}")
        if r.get("effect") == "clarify" and (r.get("applies_to") != "case" or (r.get("ask") or {}).get("kind") != "method"):
            err(f"{rid}: effect clarify needs a case rule with a method ask")
        for k, vals in list((r.get("when") or {}).items()) + list((r.get("guard") or {}).items()):
            if k in computed:
                continue
            if k not in attrs:
                err(f"{rid}: when uses undeclared attribute {k}")
                continue
            for v in vals:
                if str(v) not in [str(x) for x in attrs[k]["values"]]:
                    err(f"{rid}: value {v!r} not in vocabulary of {k}")
        if not r.get("source"):
            err(f"{rid}: no source")
        if r.get("exclude") or r.get("effect") in {"exclude", "exclude_config"}:
            if not r.get("source"):
                err(f"{rid}: exclusion without source")
        if not r.get("tests") and not r.get("untested"):
            err(f"{rid}: no tests and no `untested` reason")
        for t in r.get("tests") or []:
            if t not in golden_ids:
                err(f"{rid}: test {t} is not a golden case")
        ask = r.get("ask")
        if ask:
            if ask.get("kind") not in {"method", "plan", "lab_check"}:
                err(f"{rid}: ask.kind must be method|plan|lab_check")
            if ask.get("attribute") not in attrs:
                err(f"{rid}: ask.attribute {ask.get('attribute')} undeclared")
            elif qs.get(ask["attribute"], {}).get("kind") != ask.get("kind"):
                err(f"{rid}: ask.kind {ask.get('kind')} differs from questions.{ask['attribute']}.kind "
                    f"{qs.get(ask['attribute'], {}).get('kind')} (one source of truth)")
    for cid, c in golden["cases"].items():
        for sub_id, sub in [(cid, c)] + list((c.get("subcases") or {}).items()):
            for k, v in (sub.get("attrs") or {}).items():
                if k not in attrs:
                    err(f"golden {sub_id}: undeclared attribute {k}")
                elif str(v) not in [str(x) for x in attrs[k]["values"]]:
                    err(f"golden {sub_id}: {k}={v!r} not in vocabulary")


# ------------------------------------------------------------------ part 2: reference evaluator
def run_golden(g: dict, golden: dict, show: str | None) -> dict:
    ev = Evaluator(g)
    fired_by_case: dict[str, set] = {}
    for cid, c in golden["cases"].items():
        units = [(cid, c.get("attrs") or {}, c.get("expect") or {})]
        for sid, s in (c.get("subcases") or {}).items():
            units.append((sid, {**(c.get("attrs") or {}), **(s.get("attrs") or {})}, s.get("expect") or {}))
        # split cases: the parent is evaluated for case-level rules, subcases for rows
        all_fired, all_prem, statuses, all_method, all_plan, all_combos, all_lab = set(), {}, [], [], [], [], []
        for uid, attrs, exp in units:
            res = ev.run(attrs)
            method_q, plan_q, strength = ev.questions(attrs, res)
            lab_q = ev.lab_checks
            is_parent_of_split = uid == cid and c.get("subcases")
            all_fired |= res["fired"]
            all_prem.update(res["premises"])
            all_method += method_q
            all_lab += lab_q
            all_plan += plan_q
            all_combos += res["combinations"]
            if not is_parent_of_split:
                statuses.append(res["status"])
            if show in (cid, uid):
                print(f"\n=== {uid}  status={res['status']}  top={res['top']}")
                for rid, r in res["rows"].items():
                    print(f"  {rid} {r['status']:<10} ev={r['evidence']:<12} {', '.join(r['reasons'])}")
                print("  premises:", res["premises"])
                qs = g.get("questions", {})
                print("  method questions:")
                for k in method_q:
                    tag = "forced" if k not in strength else f"{strength[k]:.2f}"
                    text = (ev.forced_text.get(k) if k not in strength else None) or qs.get(k, {}).get("text", "")
                    print(f"    [{tag}] {k}: {text}")
                print("  plan questions:", plan_q)
                print("  lab checks (step 0):", [(k, "forced" if k not in strength else round(strength[k], 2)) for k in lab_q])
                print("  combinations:", res["combinations"])
            tag = f"golden {uid}"
            for row in exp.get("top_include", []):
                if row not in res["top"]:
                    err(f"{tag}: {row} not in top-3 {res['top']} ({res['rows'][row]['status']}: {res['rows'][row]['reasons']})")
            if exp.get("top1") and res["top"][:1] != [exp["top1"]]:
                err(f"{tag}: top-1 is {res['top'][:1]}, expected {exp['top1']}")
            if exp.get("top1_not") and res["top"][:1] == [exp["top1_not"]]:
                err(f"{tag}: {exp['top1_not']} must not be top-1")
            for row in exp.get("must_exclude", []):
                if res["rows"][row]["status"] != "excluded":
                    err(f"{tag}: {row} should be excluded, is {res['rows'][row]['status']}")
            for row in exp.get("must_exclude_config", []):
                if not res["rows"][row]["exclude_config"]:
                    err(f"{tag}: {row} should have an excluded configuration")
            if uid != cid:
                for rid in exp.get("must_fire", []):
                    if rid not in res["fired"]:
                        err(f"{tag}: rule {rid} did not fire")
        exp = c.get("expect") or {}
        tag = f"golden {cid}"
        # case status: worst subcase wins (outside_scope > insufficient > provisional)
        order = ["outside_scope", "insufficient_information", "provisional"]
        status = min(statuses, key=order.index) if statuses else "provisional"
        if exp.get("status") and exp["status"] != status:
            err(f"{tag}: status {status}, expected {exp['status']}")
        for rid in exp.get("must_fire", []):
            if rid not in all_fired:
                err(f"{tag}: rule {rid} did not fire")
        for rid, verdict in (exp.get("premises") or {}).items():
            if all_prem.get(rid) != verdict:
                err(f"{tag}: premise {rid} = {all_prem.get(rid)}, expected {verdict}")
        for attr in exp.get("ask_method", []):
            if attr not in all_method:
                err(f"{tag}: no method question about {attr} (got {list(dict.fromkeys(all_method))[:6]})")
        for attr in exp.get("lab_check", []):
            if attr not in all_lab:
                err(f"{tag}: no lab check for {attr} (got {all_lab})")
        for attr in exp.get("ask_method_not", []):
            if attr in all_method:
                err(f"{tag}: method question about {attr} should not be asked")
        for attr in exp.get("ask_plan", []):
            if attr not in all_plan:
                err(f"{tag}: no plan question about {attr} (got {list(dict.fromkeys(all_plan))})")
        for pair in exp.get("combinations", []):
            if pair not in all_combos:
                err(f"{tag}: combination {pair} not proposed")
        fired_by_case[cid] = all_fired
    # rule.tests must fire in the cases they name
    for r in g["rules"]:
        if r["step"] == "OUT":
            continue
        for t in r.get("tests") or []:
            if r["id"] not in fired_by_case.get(t, set()):
                err(f"{r['id']}: lists test {t} but does not fire there")
    return fired_by_case


H_FREEZE = ROOT / "eval" / "h_frozen.sha256"


def h_fingerprint(golden: dict) -> str:
    """Fingerprint of the TEST set (H01-H06): attrs and expectations exactly as written."""
    import hashlib
    import json
    h_cases = {k: v for k, v in golden["cases"].items() if k.startswith("H")}
    return hashlib.sha256(json.dumps(h_cases, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def check_split(g: dict, golden: dict) -> None:
    """D01-D08 = development, H01-H06 = test (AGENTS.md). H expectations are frozen; rules tested
    only on H are flagged, because a rule that no development case exercises may be fitted to H."""
    if H_FREEZE.exists():
        if H_FREEZE.read_text().split()[0] != h_fingerprint(golden):
            err("TEST set H01-H06 changed after the freeze (eval/h_frozen.sha256). Changing H expectations "
                "needs a team decision; never change them to make a rule pass")
    else:
        warnings.append("TEST set H01-H06 is not frozen yet: run with --freeze-h after the team agrees")
    h_only = [r["id"] for r in g["rules"] if r["step"] != "OUT" and r.get("tests")
              and all(t.startswith("H") for t in r["tests"])]
    if h_only:
        warnings.append("rules tested ONLY on the test set H (no development case): " + ", ".join(h_only))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="print the trace of one golden case or subcase")
    ap.add_argument("--freeze-h", action="store_true", help="write the H01-H06 fingerprint (team decision)")
    args = ap.parse_args()
    g = load(GATES)
    golden = load(GOLDEN)
    if args.freeze_h:
        H_FREEZE.write_text(h_fingerprint(golden) + "  H01-H06 expectations frozen\n")
        print(f"frozen: {H_FREEZE}")
        return 0
    validate(g, golden)
    if not errors:
        check_split(g, golden)
        fired = run_golden(g, golden, args.case)
        never = [r["id"] for r in g["rules"] if r["step"] != "OUT"
                 and not any(r["id"] in f for f in fired.values())]
        if never:
            warnings.append(f"rules that fire in no golden case: {', '.join(never)}")
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("FAIL ", e)
    dev = sum(1 for e in errors if e.startswith("golden D"))
    test = sum(1 for e in errors if e.startswith("golden H"))
    other = len(errors) - dev - test
    n_d = sum(1 for k in golden["cases"] if k.startswith("D"))
    n_h = sum(1 for k in golden["cases"] if k.startswith("H"))
    print(f"\nDEV  D01-D08: {n_d} cases, {dev} errors")
    print(f"TEST H01-H06: {n_h} cases, {test} errors (expectations: {'frozen' if H_FREEZE.exists() else 'NOT frozen'})")
    print(f"{'OK' if not errors else 'FAILED'}: {len(g['rules'])} rules, {other} structure/consistency errors, "
          f"{len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
