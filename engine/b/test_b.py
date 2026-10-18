"""Acceptance for engine B: spec 07 §5 (D01-D08, H01-H06) and a subset of §6 (T-tests).
Run: python -m pytest -q engine/b/test_b.py"""
import os
from pathlib import Path

import pytest
import yaml

from engine.b import assess_b
from engine.b.core import bucket, load_b

ROOT = Path(__file__).resolve().parents[2]
GOLD = yaml.safe_load((ROOT / "eval/golden_b.yaml").read_text(encoding="utf-8"))["cases"]


def run(cid, mode="technical"):
    old = os.environ.get("B_RANK_MODE")
    os.environ["B_RANK_MODE"] = mode
    try:
        c = GOLD[cid]
        return assess_b(c["facts"], c.get("streams"))
    finally:
        if old is None:
            os.environ.pop("B_RANK_MODE", None)
        else:
            os.environ["B_RANK_MODE"] = old


def fired(res):
    """Rules that fired on a candidate or on a combination (level: combination, R_Q2_11)."""
    out = {f["factor_id"] for co in res["cases"] for c in co["ranking"] for f in c["factor_contributions"]
           if f["outcome"] in ("MATCH", "MISMATCH") and f["selected_in_exclusive_group"]}
    return out | {f["factor_id"] for co in res["cases"] for cb in co["combinations"]
                  for f in cb["factor_contributions"] if f["outcome"] in ("MATCH", "MISMATCH")}


def unknown(res):
    return {f["factor_id"] for co in res["cases"] for c in co["ranking"] for f in c["factor_contributions"]
            if f["outcome"] == "UNKNOWN"}


@pytest.mark.parametrize("cid", sorted(GOLD))
def test_case_expectations(cid):
    exp, res = GOLD[cid]["expect"], run(cid)
    cases = res["cases"]
    if "cases" in exp:
        assert len(cases) == exp["cases"]
    for co in cases:
        lead = co["methods"][0]["method_id"] if co["methods"] else None
        if "leader_methods" in exp:
            assert lead in exp["leader_methods"], (co["case_id"], co["methods"][:3])
        if "leader_geometry" in exp:
            top = co["ranking"][0]
            assert top["configuration"]["optical_geometry"] in exp["leader_geometry"]
    assert set(exp.get("fired", [])) <= fired(res), set(exp.get("fired", [])) - fired(res)
    assert set(exp.get("unknown", [])) <= unknown(res)
    for p in exp.get("premise", []):
        assert p in {x["rule_id"] for x in res["premises"]}
    for q in exp.get("ask", []):
        assert q in {x["fact"] for co in cases for x in co["questions"]}
    if exp.get("status"):
        assert all(co["decision_status"] == exp["status"] for co in cases)
    if exp.get("deployment"):
        assert all(c["deployment_status"] == exp["deployment"] for co in cases for c in co["ranking"]
                   if c["method_id"] in ("MIR", "Fluorescence", "UV_VIS"))
    excluded_methods = {e["candidate_id"] for co in cases for e in co["excluded"] if e["level"] == "method"}
    for key, m in (("mir_not_excluded", "MIR"), ("nir_not_excluded", "NIR")):
        if exp.get(key):
            assert m not in excluded_methods
            assert any(c["method_id"] == m for co in cases for c in co["ranking"])
    if exp.get("combination"):
        assert any(cb["methods"] == exp["combination"] for co in cases for cb in co["combinations"])
    if exp.get("fluorescence_not_leader") or exp.get("fluorescence_not_direct"):
        assert all(co["methods"][0]["method_id"] != "Fluorescence" for co in cases)
    if exp.get("different_geometry_per_stream"):
        geos = {co["stream"]: co["ranking"][0]["configuration"]["optical_geometry"] for co in cases}
        assert geos["whey"] != geos["concentrate"], geos
    if exp.get("reuse_mismatch"):
        reuse = [f for co in cases for c in co["ranking"] if c["method_id"] == "MIR" and c["configuration"]["link"] == "reuse"
                 for f in c["factor_contributions"] if f["factor_id"] == "R_Q3C_08"]
        assert reuse and all(f["outcome"] == "MISMATCH" for f in reuse)
    if exp.get("new_link_branch"):
        assert any(c["configuration"]["link"] == "new" for co in cases for c in co["ranking"] if c["method_id"] == "MIR")
    if exp.get("no_viable_claim"):
        assert all(f["outcome"] != "MATCH" for co in cases for c in co["ranking"] for f in c["factor_contributions"]
                   if f["factor_id"] == "R_Q1_U03" and co["target"] == "viable_biomass")


@pytest.mark.parametrize("cid", sorted(GOLD))
@pytest.mark.parametrize("mode", ["spec", "technical"])
def test_contract_invariants(cid, mode):
    """Spec 02 §4-5: integer scores 0..9, suitability = sum, Q4 0..3, interval contains the score."""
    res = run(cid, mode)
    for co in res["cases"]:
        for c in co["ranking"]:
            s = [c["question_results"][q]["display_score"] for q in ("Q1", "Q1b", "Q2", "Q3")]
            assert all(isinstance(v, int) and 0 <= v <= 9 for v in s)
            assert c["suitability"] == sum(s) and 0 <= c["suitability"] <= 36
            assert 0 <= c["q4_score"] <= 3
            lo, hi = c["suitability_interval"]
            assert lo <= c["suitability"] <= hi
            for f in c["factor_contributions"]:
                assert f["outcome"] in ("MATCH", "MISMATCH", "UNKNOWN", "NOT_APPLICABLE")
                if f["outcome"] == "UNKNOWN":
                    assert f["effect"] == 0
        for e in co["excluded"]:   # Score=0 is never a shortcut for an exclusion: a proven reason exists
            assert e["excluded_by"] and all(x["reason"] and x["rule_id"] for x in e["excluded_by"])
        assert len(co["questions"]) <= 3


def test_bucket_table():
    _, reg = load_b()
    thr = reg["bucket_thresholds"]
    vals = [bucket(r, thr) for r in range(-12, 13)]
    assert vals == sorted(vals) and vals[0] == 0 and vals[-1] == 9
    assert bucket(0, thr) == 4 and bucket(-6, thr) == 0 and bucket(6, thr) == 9


def test_T01_empty_temperature_is_unknown_not_ambient():
    res = assess_b({"MeasurementTask.target": ["api"], "Sample.matrix": "polymer", "Sample.physical_form": "melt"})
    t = res["facts"]["ProcessContext.temperature_range"]
    assert t["value"] is None and t["status"] == "unknown" and t["source"] is None


def test_fact_record_has_value_unit_source_status():
    """Fact record: value + unit/category + source + status; missing data is never a fact."""
    res = assess_b({"MeasurementTask.target": {"value": ["water"], "status": "reported", "quote": "Wasser im Öl"},
                    "Sample.matrix": {"value": "petroleum", "status": "confirmed_experiment", "source": "lab test T1"},
                    "Sample.phase": {"value": "liquid", "status": "inferred", "source": "derived from 'Öl'"}})
    f = res["facts"]
    for rec in f.values():
        assert set(rec) >= {"value", "unit_or_category", "source", "status"}
        assert rec["status"] in ("reported", "inferred", "unknown", "confirmed_experiment", "confirmed_expert", "conflicting")
        assert (rec["value"] is None) == (rec["status"] in ("unknown", "conflicting"))
    assert f["MeasurementTask.target"]["source"] == "client_text" and f["MeasurementTask.target"]["quote"]
    assert f["Sample.matrix"]["status"] == "confirmed_experiment"
    assert f["Sample.optical_properties.opacity"]["status"] == "unknown"
    assert f["ProcessContext.deployment_preference"]["status"] == "inferred"   # product scope, not the client
    with pytest.raises(ValueError):
        assess_b({"Sample.matrix": {"value": "dairy", "status": "guessed"}})


def test_T02_absent_mention_is_not_absent_fluorescence():
    a = assess_b({"MeasurementTask.target": ["api"], "Sample.physical_form": "powder", "Sample.matrix": "pharma_blend"})
    b = assess_b({"MeasurementTask.target": ["api"], "Sample.physical_form": "powder", "Sample.matrix": "pharma_blend",
                  "Sample.optical_properties.fluorescence": "absent"})
    def r02(res):
        return {f["outcome"] for c in res["cases"][0]["ranking"] if c["method_id"] == "Raman"
                for f in c["factor_contributions"] if f["factor_id"] == "R_Q1_R02"}
    assert r02(a) == {"UNKNOWN"} and r02(b) == {"MATCH"}


def test_hard_exclusion_needs_known_facts():
    """Spec 02 §3: contact prohibited excludes contact pairs only; unknown contact excludes nothing."""
    base = {"MeasurementTask.target": ["water"], "Sample.matrix": "petroleum", "Sample.phase": "liquid"}
    assert all(x["rule_id"] != "R_Q2_03" for e in assess_b(base)["cases"][0]["excluded"] for x in e["excluded_by"])
    ex = assess_b({**base, "Sample.sample_state_constraints.contact": "prohibited"})["cases"][0]
    assert ex["excluded"] and all(e["level"] == "method_interface" for e in ex["excluded"])
    assert ex["ranking"], "non-contact interfaces stay"


def test_deterministic():
    assert run("D01") == run("D01")


# ---------------------------------------------------------------------------------- spec 07 §6, T04-T10
def test_T04_unknown_that_changes_the_leader_is_a_high_question():
    """D01: matrix fluorescence is unknown; 'present' moves the lead away from Raman/NIR tie -> high + why + rule ids."""
    co = run("D01")["cases"][0]
    s = next(s for s in co["sensitivity"] if s["fact"] == "Sample.optical_properties.fluorescence")
    assert s["impact"] == "high"
    assert any(sc.get("leader") != s["baseline_leader"] or sc.get("excluded_change") for sc in s["scenarios"])
    q = next(q for q in co["questions"] if q["fact"] == "Sample.optical_properties.fluorescence")
    assert q["priority"] == "high" and q["why"] and "R_Q1_R02" in q["rule_ids"]


def test_T05_top3_only_change_is_medium_and_low_is_not_asked():
    meds = 0
    for cid in sorted(GOLD):
        for co in run(cid)["cases"]:
            asked = {q["fact"] for q in co["questions"]}
            for s in co["sensitivity"]:
                if s["impact"] == "low":
                    assert s["fact"] not in asked, (cid, s["fact"])
                if s["impact"] == "medium":
                    meds += 1   # medium never comes from a leader or exclusion change
                    assert all("leader" not in sc and "top_candidates" in sc for sc in s["scenarios"]), (cid, s)
            assert all(q["priority"] in ("high", "medium") for q in co["questions"] if q["fact"] != "MeasurementTask.target_definition")
    assert meds, "no medium sensitivity anywhere: T05 would not be exercised"


def test_T06_sensitivity_sees_the_excluded_assembly_branch():
    """H04-like: actual cable profile unknown. The scenario 'profile confirmed' excludes the reuse assembly
    (R_Q3P_03 hard): sensitivity must report that branch, while the new-link MIR branch stays."""
    facts = {**GOLD["H04"]["facts"]}
    facts.pop("ProcessContext.assets.fiber_profile")
    co = assess_b(facts)["cases"][0]
    s = next(s for s in co["sensitivity"] if s["fact"] == "ProcessContext.assets.fiber_profile")
    assert s["impact"] == "high"
    changed = {c for sc in s["scenarios"] for c in sc.get("excluded_change", [])}
    assert any(c.startswith("MIR|") and c.endswith("|reuse") for c in changed), changed
    assert any(c["method_id"] == "MIR" and c["configuration"]["link"] == "new" for c in co["ranking"])


def test_T07_missing_method_interface_edge_is_unknown_not_exclusion():
    from engine.b.core import Ctx, eval_rule
    cat, reg = load_b()
    r01 = next(r for r in reg["rules"] if r["id"] == "R_Q2_01")
    x = Ctx(cat, {"Sample.phase": "liquid"}, "MIR", iface=cat["interfaces"]["NIR_DIFFUSE_PROBE"], case_target="water")
    f = eval_rule(r01, x)
    assert f["outcome"] == "UNKNOWN" and f["effect"] == 0 and f["exclusion"] is None
    assert min(f["possible"]) == -3   # a later proof of incompatibility could still count against it
    x = Ctx(cat, {"Sample.phase": "liquid"}, "MIR", iface=cat["interfaces"]["MIR_ATR_PROBE"], case_target="water")
    assert eval_rule(r01, x)["outcome"] == "MATCH"


def _t08(rating):
    facts = {**GOLD["D07"]["facts"], "ProcessContext.temperature_c": {"value": [20, 180], "unit": "degC", "quote": "20-180 C"},
             "Configuration.operating_envelope.temperature_c": {"value": {"MIR_ATR_PROBE": rating},
                                                                "status": "confirmed_expert", "source": "data sheet"}}
    return assess_b(facts, with_sensitivity=False)["cases"][0]


def test_T08_temperature_range_checked_at_both_ends_other_probe_stays():
    for rating in ([0, 150], [30, 200]):   # max above the rating; min below the rating
        co = _t08(rating)
        ex = [e for e in co["excluded"] if e["candidate_id"].startswith("MIR|MIR_ATR_PROBE|")]
        assert ex and all(e["level"] == "configuration" for e in ex), rating
        assert {x["rule_id"] for e in ex for x in e["excluded_by"]} == {"R_Q3P_01"}
        mir = [c for c in co["ranking"] if c["method_id"] == "MIR"]
        assert mir and all(c["interface_id"] != "MIR_ATR_PROBE" for c in mir), "another MIR probe stays a candidate"
    ok = _t08([0, 200])
    probe = next(c for c in ok["ranking"] if c["interface_id"] == "MIR_ATR_PROBE")
    f = {f["factor_id"]: f for f in probe["factor_contributions"]}
    assert f["R_Q3P_01"]["outcome"] == "MATCH"
    assert f["R_Q3C_01"]["selected_in_exclusive_group"] is False   # component replaces the concept row (T13 family)


def test_T09_lod_without_loq_is_no_quantitative_pass():
    facts = {**GOLD["D06"]["facts"], "MeasurementTask.performance_requirements":
             {"value": "given", "quote": "detection limit 50 ppm is enough"}}
    co = assess_b(facts, with_sensitivity=False)["cases"][0]
    for c in co["ranking"]:
        q1b = c["question_results"]["Q1b"]
        f = {f["factor_id"]: f for f in c["factor_contributions"]}
        assert f["R_Q1B_02"]["outcome"] == "UNKNOWN" and f["R_Q1B_02"]["code"] == "NO_SCOPED_PERFORMANCE_PROFILE"
        assert f["R_Q1B_04"]["outcome"] == "UNKNOWN"   # achieved error vs allowed error: no profile
        assert q1b["status"] == "provisional"
    assert co["decision_status"] != "assessed"


def test_T10_ppm_without_basis_is_not_compared_with_percent():
    facts = {**GOLD["D06"]["facts"], "MeasurementTask.target_range": {"value": "given", "unit": "ppm", "quote": "below 500 ppm"}}
    res = assess_b(facts, with_sensitivity=False)
    assert res["facts"]["MeasurementTask.target_range"]["unit_or_category"] == "ppm"   # kept, not converted
    for c in res["cases"][0]["ranking"]:
        rng = [f for f in c["factor_contributions"] if f["group"] == "range"]
        assert rng and all(f["outcome"] == "UNKNOWN" and f["effect"] == 0 for f in rng)
        assert c["question_results"]["Q1b"]["group_totals"]["range"] == 0
