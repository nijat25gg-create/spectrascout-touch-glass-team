"""Recompute the engine part of the examples from the C3 example (gates engine).

    python contracts/regen_assessment_example.py      # after any change to rules/gates.yaml or engine/
- C4 = C3.features + C3.attributes (v0.3)
- C5 = engine.score_methods(C4): ranked/rejected/assessment, all from the gates
- C6.scoring = C5
Then run contracts/check_contracts.py (it rebuilds C8 and C1b). engine/test_gates.py fails while stale.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.models import Extraction, ScoreInput  # noqa: E402
from engine import score_methods  # noqa: E402

EX = ROOT / "contracts" / "examples"


def _load(name):
    return json.loads((EX / f"{name}.example.json").read_text(encoding="utf-8"))


def _save(name, d):
    (EX / f"{name}.example.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("updated", name)


c3 = Extraction.model_validate(_load("C3_extraction"))
c4 = _load("C4_score_input")
c4["features"] = json.loads(c3.features.model_dump_json())
c4["attributes"] = json.loads(json.dumps([a.model_dump() for a in c3.attributes or []]))
_save("C4_score_input", c4)
c5 = json.loads(score_methods(ScoreInput.model_validate(c4)).model_dump_json())
_save("C5_scoring", c5)
c6 = _load("C6_explain_input")
c6["scoring"] = c5
_save("C6_explain_input", c6)
