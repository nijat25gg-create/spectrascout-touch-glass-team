---
description: Add a rule to rules/gates.yaml (the gates engine) in the correct format. Use when someone describes a chemistry rule in words, e.g. "если матрица водная, MIR рискованно".
---
1. Map the description to attributes and values that exist in `rules/gates.yaml` (`attributes:`). If no attribute fits, stop and say which one is missing (adding an attribute also needs `contracts/models.py` AttributeName and the step-A prompt).
2. Write the rule: id UPPER-CASE, step (Q1 task, Q2 signal, Q3 interface/fiber, Q4 premises/evidence), applies_to (case, method, row), targets, when (and guard if an input must be known), effect, on_unknown, because (one line an AFS expert understands), source (AFS page; no page, no rule), tests (golden case ids, or `untested` with a reason). `exclude` only for physical impossibility or a mandatory condition. on_unknown must never be stricter than the effect of the known bad value. Never write a rule because of an H01-H06 result.
3. Show the YAML to the user before inserting.
4. Insert next to related rules and run: `python rules/check_gates.py` (DEV and TEST must stay 0 errors), `python -m pytest -q engine/test_gates.py`, `python rules/mutate_gates.py`, then `python rules/rules_table.py` and `python contracts/regen_assessment_example.py`. Show what changed (`python rules/check_gates.py --case <id>`).
5. Suggest running @agent-rules-reviewer on it. Chemistry stays draft until Nikita confirms.
