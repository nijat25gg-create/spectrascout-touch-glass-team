"""python -m engine.selftest  — C4 -> C5 on the gates engine (C4 example + edge cases) and number -> class.

The old points engine (rules/rules.yaml) is retired; its selftest is in legacy/selftest_v02.py.
"""
import os

os.environ.setdefault("ENGINE", "ab")   # gates selftest: since 18.10 ENGINE=b is the default

from contracts.models import Extraction, ScoreInput  # noqa: E402
from engine import features_to_attributes, score_methods  # noqa: E402
from llm.client import example  # noqa: E402

c3 = Extraction.model_validate(example("C3_extraction.example.json"))
c4 = ScoreInput.model_validate(example("C4_score_input.example.json"))
res = score_methods(c4)
print("rules:", res.rules_version, "| case:", res.assessment.decision_status, res.assessment.selected)
for r in res.ranked:
    print(f"  #{r.rank} {r.method:13} {r.score_total:5}  {r.mode:20} conf={r.confidence}  {r.probe}")
    for s in r.scores:
        print(f"       {s.criterion:32} {s.score:+5}  {s.rule_id}")
for r in res.rejected:
    print(f"  x {r.method:13} {'BLOCK' if r.blocker else 'other'} {r.rule_id}: {r.reason}")
assert res.rules_version.startswith("rules-gates"), res.rules_version
assert res.ranked and res.ranked[0].method == "nir", "moisture in powder should rank NIR first"
assert len({r.method for r in res.ranked}) == len(res.ranked), "one entry per method"
assert {r.method for r in res.ranked}.isdisjoint({r.method for r in res.rejected})
assert {r.method for r in res.ranked} | {r.method for r in res.rejected} == {
    "uv_vis", "nir", "mir", "raman", "fluorescence", "scattering"}, "every method exactly once"
assert score_methods(c4) == res, "engine must be deterministic"
assert res.assessment is not None and res.assessment.selected[0] == "K03"

# C4 attributes (v0.3) replace the feature fallback; on the example both give the same decision
features_only = score_methods(c4.model_copy(update={"attributes": None}))
assert c4.attributes and [r.method for r in features_only.ranked] == [r.method for r in res.ranked]


def case(**kw):
    """v0.2 caller: features only (no attributes), so the feature fallback is used"""
    d = c4.model_dump()
    d["attributes"] = None
    for k, v in kw.items():
        d["features"][k] = {"value": v, "status": "known"}
    return ScoreInput.model_validate(d)


# a case that is not provisional recommends nothing, every method gets a reason
gas = score_methods(case(phase="gas"))
assert gas.assessment.decision_status == "outside_scope" and gas.ranked == []
assert all(r.reason for r in gas.rejected) and len(gas.rejected) == 6
# feature fallback mapping
assert features_to_attributes(case(phase="liquid", turbidity="opaque").features)["optical_density"] == "opaque"
print("all engine checks OK")

# number -> class (engine/numeric.py), used by the backend when the expert types a value
from engine.numeric import classify  # noqa: E402
assert classify("temperature", "80 °C") == ("temperature_class", "elevated")
assert classify("pressure", "500 mbar") == ("pressure_class", "vacuum")
assert classify("distance_to_instrument", "50 m") == ("distance_class", "long")
assert classify("concentration_range", "1-5 %") == ("concentration_level", "low_percent")
assert classify("temperature", "warm") is None
print("numeric OK")
