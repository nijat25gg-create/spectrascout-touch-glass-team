---
paths:
  - "rules/**"
  - "engine/**"
---
The only rules engine is rules/gates.yaml (since 18.10; rules/rules.yaml retired to legacy/, do not edit it).
Do not invent limits the sources do not give (no fiber lengths, temperatures or accuracies without a page).
The engine must stay deterministic: same attributes → same result. Mark unverified chemistry (draft until Nikita confirms).
rules/gates.yaml: each rule needs id, step, applies_to, targets, when, effect, on_unknown,
because, source (page) and tests (golden case ids, or `untested` with a reason). Run
`python rules/check_gates.py`, `python -m pytest -q engine/test_gates.py`, `python rules/mutate_gates.py`,
then `python rules/rules_table.py`, `python contracts/regen_assessment_example.py` and `python -m engine.selftest`.
on_unknown must never be stricter than the effect of the known bad value (monotonicity).
