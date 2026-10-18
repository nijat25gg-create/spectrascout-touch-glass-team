# Engine

Owner: rules engine. Since 18.10 the only engine is the **gates engine** on [`rules/gates.yaml`](../rules/gates.yaml)
(team decision; the old points engine on `rules.yaml` is in [`legacy/`](../legacy/README.md), reference only).

| Function | Contract | What |
|---|---|---|
| `score_methods(ScoreInput) -> Scoring` | C4 → C5 | `ranked` / `rejected` filled from the gates (one entry per method, gates order), `assessment` = full gates result |
| `gates.assess(attrs) -> GatesAssessment` | — | row statuses, evidence, premises, questions (Gadzhi's enumeration), lab checks, trace |
| `gates.assess_extraction(c3_or_c8)` | C3/C8 → assessment | same, from `.attributes` |
| `gates.completeness_score_fn(request)` | — | adapter for `completeness`: top-1 row + status, plus `ignored` |
| `paths.path_json(attrs)` / `python -m engine.paths` | — | decision path for the screen and `docs/decision-paths.md` |
| `numeric.classify(param, text)` | — | number → feature class (backend, expert edits) |

C4 `attributes` (v0.3) are the engine input. Only for a v0.2 caller without attributes the engine derives them
from the 12 features (`features_to_attributes`, coarse); the two are never mixed.
Deterministic: the same input always gives the same output.

## Run

```bash
python -m engine.selftest              # C4 example + edge cases (gates)
python -m pytest -q engine/test_gates.py
python rules/check_gates.py            # golden: DEV D01-D08, TEST H01-H06 (frozen)
python rules/mutate_gates.py           # every rule/engine mutation must be caught
LLM_MOCK=1 python run_case.py          # whole chain without backend
```
