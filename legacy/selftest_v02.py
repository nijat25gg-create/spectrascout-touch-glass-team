"""LEGACY: python legacy/selftest_v02.py (was python -m engine.selftest)  — runs the engine on the C4 example and a few edge cases."""
import sys, pathlib; sys.path[:0] = [str(pathlib.Path(__file__).parent), str(pathlib.Path(__file__).parents[1])]
from contracts.models import ScoreInput
from score_v02 import score_methods  # legacy
from llm.client import example

c4 = ScoreInput.model_validate(example("C4_score_input.example.json"))
res = score_methods(c4)
print("rules:", res.rules_version)
for r in res.ranked:
    print(f"  #{r.rank} {r.method:13} {r.score_total:5}  {r.mode:20} conf={r.confidence}")
    for s in r.scores:
        print(f"       {s.criterion:30} {s.score:+5}  {s.rule_id}")
for r in res.rejected:
    print(f"  x {r.method:13} {'BLOCK' if r.blocker else 'low  '} {r.rule_id}: {r.reason}")
assert res.ranked[0].method == "nir", "moisture in powder should rank NIR first"
assert score_methods(c4) == res, "engine must be deterministic"


def case(**kw):
    d = c4.model_dump()
    for k, v in kw.items():
        d["features"][k] = {"value": v, "status": "known"}
    return ScoreInput.model_validate(d)


aq = score_methods(case(phase="liquid", water_level="high", analyte_type="organic_compound",
                        concentration_level="low_percent", turbidity="clear"))
print("aqueous organic:", [r.method for r in aq.ranked])
assert aq.ranked[0].method == "raman"
far = score_methods(case(phase="liquid", analyte_type="organic_compound", water_level="none", distance_class="long"))
assert any(r.method == "mir" and r.blocker for r in far.rejected), "MIR must be blocked for long fibers"
print("all engine checks OK")

# number → class (engine/numeric.py), used by the backend when the expert types a value
from engine.numeric import classify
assert classify("temperature", "80 °C") == ("temperature_class", "elevated")
assert classify("pressure", "500 mbar") == ("pressure_class", "vacuum")
assert classify("distance_to_instrument", "50 m") == ("distance_class", "long")
assert classify("concentration_range", "1-5 %") == ("concentration_level", "low_percent")
assert classify("temperature", "warm") is None
print("numeric OK")
