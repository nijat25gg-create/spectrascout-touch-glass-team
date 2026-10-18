"""Tests for engine.gates (v0.3 draft).

    python -m pytest engine/test_gates.py -q      # or: python -m engine.test_gates
The golden expectations themselves are checked by rules/check_gates.py; here we test the public API.
"""
import json
from pathlib import Path

from contracts.models import Extraction, GatesAssessment, Scoring
from engine.gates import Evaluator, assess, assess_extraction, completeness_score_fn
from engine.gates_loader import load_gates, load_yaml

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = load_yaml(ROOT / "eval" / "golden_cases.yaml")["cases"]
H04 = GOLDEN["H04"]["attrs"]


def _units():
    for cid, c in GOLDEN.items():
        if c.get("subcases"):
            for sid, s in c["subcases"].items():
                yield sid, {**c["attrs"], **s.get("attrs", {})}
        else:
            yield cid, c["attrs"]


def test_every_row_once_and_valid_contract():
    g = load_gates()
    for uid, attrs in _units():
        a = assess(attrs)
        GatesAssessment.model_validate(a.model_dump())
        assert sorted(r.row for r in a.rows) == sorted(g["catalog"]), uid
        assert len(a.selected) <= 3, uid


def test_same_result_as_reference_evaluator():
    ev = Evaluator(load_gates())
    for uid, attrs in _units():
        res = ev.run(attrs)
        a = assess(attrs)
        assert a.selected == res["top"] and a.decision_status == res["status"], uid


def test_deterministic():
    assert assess(H04) == assess(H04)


def test_exclusions_are_traceable_to_a_sourced_rule():
    for uid, attrs in _units():
        a = assess(attrs)
        for r in a.rows:
            if r.status == "excluded":
                steps = [t for t in a.trace if t.target == r.row and t.effect == "exclude"]
                assert steps and all(t.source for t in steps), (uid, r.row)


def test_h04_premises_and_forced_question():
    a = assess(H04)
    flags = {p.rule_id: p.verdict for p in a.premise_flags}
    assert flags == {"P-FIBER-RANGE": "contradicted", "P-APPROVE-WITHOUT-DATA": "not_supported"}
    first = a.questions[0]
    assert first.attribute == "link_confirmed" and first.forced and first.kind == "method"


def test_lab_checks_are_not_client_questions():
    a = assess(GOLDEN["D01"]["attrs"])
    assert "matrix_fluorescence" in [q.attribute for q in a.lab_checks]
    assert "matrix_fluorescence" not in [q.attribute for q in a.questions]


def test_jev_probabilities_weight_question_strength():
    uniform = {q.attribute: q.strength for q in assess(H04).questions if q.kind == "method"}
    # Jev thinks the oil is almost surely opaque: only the 'opaque' answer keeps the decision -> weaker
    probs = {"optical_density": {"opaque": 0.94, "clear": 0.02, "turbid": 0.02, "varies": 0.02}}
    weighted = {q.attribute: q.strength for q in assess(H04, probs).questions if q.kind == "method"}
    assert uniform["optical_density"] == 0.75
    assert "optical_density" not in weighted          # 0.06 of the mass changes the decision < 0.3
    probs = {"optical_density": {"clear": 0.9, "opaque": 0.1}}
    weighted = {q.attribute: q.strength for q in assess(H04, probs).questions if q.kind == "method"}
    assert weighted["optical_density"] == 0.9          # the likely answer changes the decision -> strong


def test_extraction_example_chain():
    c3 = Extraction.model_validate(json.loads((ROOT / "contracts/examples/C3_extraction.example.json").read_text()))
    a = assess_extraction(c3)
    c5 = Scoring.model_validate(json.loads((ROOT / "contracts/examples/C5_scoring.example.json").read_text()))
    assert c5.assessment == a, "C5 example must be the engine output for the C3 example (regenerate it)"
    assert a.selected[0] == "K03"   # moisture in a pharma powder: NIR diffuse reflection (S01 p.10, p.14-15)


def test_completeness_adapter_shape():
    req = {"attributes": {k: {"value": v, "status": "known"} for k, v in H04.items()}}
    req["attributes"]["optical_density"] = {"value": None, "status": "unknown"}
    out = completeness_score_fn(req)
    assert set(out) == {"selected", "decision_status", "ignored"} and len(out["selected"]) <= 1


# ---------------------------------------------------------------- regressions from the 18.10 adversarial review
# Synthetic inputs (not H cases). Each pins one general behaviour.
PHARMA = {"target_defined": "yes", "domain": "pharma_solid", "sample_form": "powder", "target_kind": "api"}
DAIRY = {"target_defined": "yes", "domain": "dairy", "sample_form": "liquid", "optical_density": "opaque", "target_kind": "fat"}


def test_known_bad_fact_never_better_than_unknown():
    tissue = {"target_defined": "yes", "domain": "tissue", "sample_form": "soft_solid", "target_kind": "tissue_type",
              "matrix_aqueous": "yes", "intended_use": "pilot"}
    assert assess(tissue).selected == assess({**tissue, "matrix_fluorescence": "high"}).selected == []
    contaminant = {"target_defined": "yes", "domain": "other", "sample_form": "liquid", "target_kind": "contaminant",
                   "matrix_aqueous": "yes", "target_class": "trace"}
    assert "K05" not in assess({**contaminant, "matrix_fluorescence": "high"}).selected


def test_wrong_fiber_keeps_the_method_with_another_configuration():
    a = assess({**DAIRY, "existing_fiber": "polycrystalline"})
    assert a.selected[0] == "K03"                       # NIR reflection stays first, with a fiber swap
    b = assess({**DAIRY, "existing_fiber": "polycrystalline", "distance": "outside_area"})
    assert b.decision_status == "provisional"


def test_premises_only_about_the_clients_own_proposal():
    assert assess({**DAIRY, "existing_fiber": "silica_vis_nir"}).premise_flags == []
    for m in ("nir", "raman"):
        a = assess({**PHARMA, "client_method": m, "asks": "approve_concept"})
        assert a.premise_flags == [], m                # its best row is a candidate with application evidence


def test_standard_silica_is_a_full_fit_for_nir():
    a = assess({**PHARMA, "existing_fiber": "silica_vis_nir"})
    assert a.selected[0] == "K03"
    assert not any(t.rule_id == "L-FIBER-PARTIAL" and t.target == "K03" for t in a.trace)


def test_sample_form_outside_table1_is_not_recommended():
    a = assess({"target_defined": "yes", "domain": "dairy", "sample_form": "soft_solid", "optical_density": "turbid",
                "target_kind": "fat"})
    assert "K02" not in a.selected                      # transmission probe is liquid-only
    gas = assess({"target_defined": "yes", "domain": "dairy", "sample_form": "gas", "target_kind": "water"})
    assert gas.decision_status == "outside_scope" and gas.selected == []


def test_biomass_turbidity_needs_no_chromophore():
    a = assess({"target_defined": "yes", "domain": "bioprocess", "sample_form": "liquid", "target_kind": "biomass",
                "optical_density": "turbid", "chromophore": "no"})
    assert a.decision_status == "provisional" and a.selected


def test_insufficient_case_always_asks_something():
    for attrs in ({"target_defined": "partial"}, {"target_defined": "yes"},
                  {"target_defined": "yes", "domain": "other", "sample_form": "liquid", "target_kind": "contaminant"}):
        a = assess(attrs)
        if a.decision_status == "insufficient_information":
            assert [q for q in a.questions if q.kind == "method"], attrs


def test_invalid_input_is_ignored_and_reported():
    res = Evaluator(load_gates()).run({"existing_fiber": "silica", "foo": 1, "sample_form": None, "streams": True})
    assert len(res["invalid"]) == 3 and res["status"] == "insufficient_information"
    assert assess({"existing_fiber": "silica"}).decision_status == "insufficient_information"   # no crash


def test_jev_weights_with_unknown_keys_fall_back_to_uniform():
    q = {x.attribute: x.strength for x in assess(H04, {"optical_density": {"Opaque": 0.9, "Clear": 0.1}}).questions}
    assert q["optical_density"] == 0.75


def test_completeness_adapter_is_cheap_and_consistent():
    import time
    req = {"attributes": {k: {"value": v, "status": "known"} for k, v in H04.items()}}
    t = time.time()
    out = completeness_score_fn(req)
    assert time.time() - t < 0.5   # generous: CI machines are slow; typical 0.3 ms
    assert out == {"selected": assess(H04).selected[:1], "decision_status": assess(H04).decision_status,
                   "ignored": []}


def test_probe_false_keeps_existing_fiber_out_of_the_enumeration():
    import copy
    g = copy.deepcopy(load_gates())
    d07 = GOLDEN["D07"]["attrs"]                         # MIR ATR is top-1: the fiber type would flip it
    asked = lambda gg: [q.attribute for q in assess(d07, g=gg).questions if q.kind == "method"]
    assert "existing_fiber" not in asked(g)
    g["questions"]["existing_fiber"]["probe"] = True
    assert "existing_fiber" in asked(g)


if __name__ == "__main__":
    import sys
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} tests passed")
    sys.exit(0)


# ---------------------------------------------------------------- 18.10 review: gaps the mutation test missed
import copy  # noqa: E402

DAIRY_U = {"target_defined": "yes", "domain": "dairy", "sample_form": "liquid", "target_kind": "fat"}


def test_opaque_is_monotone_for_transmission():
    unknown = assess(DAIRY_U)
    opaque = assess({**DAIRY_U, "optical_density": "opaque"})
    clear = assess({**DAIRY_U, "optical_density": "clear"})
    assert "K02" in unknown.selected and "optical_density" in [q.attribute for q in unknown.questions]
    assert "K02" not in opaque.selected                     # a known opaque liquid never gets a transmission probe
    assert clear.selected[0] == "K02"


def test_approval_needs_the_clients_own_configuration():
    # K01 MIR stays a candidate but only with another fiber (exclude_config): the concept is not approvable
    a = assess({"target_defined": "yes", "domain": "petroleum", "sample_form": "liquid", "target_kind": "water",
                "client_method": "mir", "existing_fiber": "silica_vis_nir", "distance": "at_process",
                "asks": "approve_concept", "optical_density": "opaque"})
    k01 = next(r for r in a.rows if r.row == "K01")
    assert k01.status == "candidate" and any(x.endswith(":exclude_config") for x in k01.risks)
    assert {p.rule_id: p.verdict for p in a.premise_flags}.get("P-APPROVE-WITHOUT-DATA") == "not_supported"


def test_approval_needs_support_not_only_a_candidate_row():
    a = assess({"target_defined": "yes", "domain": "petroleum", "sample_form": "liquid", "target_kind": "water",
                "optical_density": "clear", "client_method": "raman", "asks": "approve_concept"})
    raman = [r for r in a.rows if r.method == "raman"]
    assert all(r.evidence == "none" for r in raman)
    assert {p.rule_id: p.verdict for p in a.premise_flags}.get("P-APPROVE-WITHOUT-DATA") == "not_supported"


def test_clarify_is_forced_for_a_partial_target():
    a = assess({"domain": "bioprocess", "sample_form": "liquid", "optical_density": "varies",
                "target_defined": "partial", "targets_count": "2plus"})
    q = {x.attribute: x for x in a.questions if x.kind == "method"}
    assert "target_defined" in q and q["target_defined"].forced


def test_outside_scope_only_answers_are_not_method_questions():
    attrs = {**DAIRY_U, "optical_density": "opaque"}
    assert "intended_use" not in [q.attribute for q in assess(attrs).questions if q.kind == "method"]
    g = copy.deepcopy(load_gates())
    g["question_policy"]["ignore_outside_scope_only"] = False
    g["question_policy"]["min_strength"] = 0.2           # 'clinical' is 1 of 4 values = 0.25
    assert "intended_use" in [q.attribute for q in assess(attrs, g=g).questions if q.kind == "method"]


def test_max_method_and_no_optical_density_for_solids():
    g = copy.deepcopy(load_gates())
    g["question_policy"]["max_method"] = 1
    assert len([q for q in assess({}, g=g).questions if q.kind == "method"]) == 1
    a = assess({"sample_form": "powder"})
    assert a.decision_status == "insufficient_information"
    assert "optical_density" not in [q.attribute for q in a.questions if q.kind == "method"]


def test_empty_input_gets_three_basic_questions():
    qs = [q.attribute for q in assess({}).questions if q.kind == "method"]
    assert len(qs) >= 3 and "target_defined" in qs


def test_nothing_selected_unless_provisional():
    a = assess({"target_defined": "no", "domain": "pharma_solid", "sample_form": "powder", "target_kind": "api"})
    assert a.decision_status == "insufficient_information" and a.selected == []


def test_correct_mir_fiber_adds_no_fiber_risk():
    base = {"target_defined": "yes", "domain": "polymer_melt", "sample_form": "paste_melt", "target_kind": "api"}
    for fib in ("polycrystalline", "hollow_waveguide"):
        k01 = next(r for r in assess({**base, "existing_fiber": fib}).rows if r.row == "K01")
        assert not any(x.startswith("L-FIBER-PARTIAL") for x in k01.reasons), (fib, k01.reasons)


def test_malformed_inputs_do_not_crash():
    assert completeness_score_fn({"domain": "dairy"})["decision_status"]
    assert completeness_score_fn({"attributes": {"domain": {"value": "dairy", "status": "known"}}})
    ev = Evaluator(load_gates())
    assert ev.run([("domain", "dairy")])["invalid"]
    assess(DAIRY_U, probs={"optical_density": [0.5]})
    assess(DAIRY_U, probs={"optical_density": {"opaque": -1, "clear": float("nan")}})
    a = assess({**DAIRY_U, "existing_fiber": "silica"})
    assert a.ignored_inputs and "existing_fiber" in a.ignored_inputs[0]


def test_blend_potency_application_does_not_support_moisture():
    a = assess({"target_defined": "yes", "domain": "pharma_solid", "sample_form": "powder", "target_kind": "water"})
    assert "K05" not in a.selected                        # Raman: blend potency (API) evidence, not water
    assert {r.row: r.evidence for r in a.rows}["K03"] == "physics_only"


# ---------------------------------------------------------------- completeness adapter: status vocabulary (18.10)
# The unified model design names the statuses stated / inferred;
# the C3 contract names them known / assumed. Both must count as facts; a status the adapter does not know
# must be reported, never silently turn the case into insufficient_information.

def _req(status):
    return {"attributes": {k: {"value": v, "status": status} for k, v in H04.items()}}


def test_completeness_adapter_accepts_both_status_vocabularies():
    expected = completeness_score_fn(_req("known"))
    assert expected["decision_status"] == "provisional"
    for status in ("stated", "inferred", "assumed", "Known", " stated "):
        out = completeness_score_fn(_req(status))
        assert (out["selected"], out["decision_status"]) == (expected["selected"], expected["decision_status"]), status
        assert out["ignored"] == []


def test_completeness_adapter_reports_unrecognised_status_instead_of_dropping_it_silently():
    out = completeness_score_fn(_req("confirmed"))
    assert len(out["ignored"]) == len(H04) and all("confirmed" in x for x in out["ignored"])


def test_completeness_adapter_unknown_and_conflicting_stay_unknown():
    for status in ("unknown", "conflicting", "not_stated"):
        out = completeness_score_fn(_req(status))
        assert out["decision_status"] == completeness_score_fn({"attributes": {}})["decision_status"]
        assert out["ignored"] == []
