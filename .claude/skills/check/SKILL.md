---
description: Run all project checks (contracts, engine, llm mock, end-to-end, backend tests). Use before a commit or PR, or when the user says "check" or "проверь".
---
Run in order (python3 on macOS, python on Windows; on Windows set $env:LLM_MOCK=1):
1. python contracts/check_contracts.py
2. python -m engine.selftest
3. LLM_MOCK=1 python -m llm.selftest
4. LLM_MOCK=1 python run_case.py
5. if backend/tests exists: cd backend && pytest -q
6. python -m pytest -q engine/test_gates.py          (gates engine, v0.3)
7. python rules/check_gates.py                       (golden: DEV D01-D08 and TEST H01-H06 must both show 0 errors)
8. after a change in rules/gates.yaml or engine/gates.py also: python rules/mutate_gates.py (all mutations caught),
   python contracts/regen_assessment_example.py, python rules/rules_table.py, python -m engine.paths
Report one line per step: OK or FAIL + first error line. If something fails, propose the fix but do not apply it without asking.
