---
description: Evaluate the pipeline on all labelled test cases and update eval/results.md. Use for accuracy numbers and after rule changes.
---
Delegate to the case-evaluator subagent. If eval/run_eval.py does not exist yet, say so and offer to create it.
Gates (v0.3): `python rules/check_gates.py`; step A: `python eval/extract_eval.py --live` (real API, only if the
user asks; reads materials/ locally) or `--from-dir DIR`; own synthetic cases: `--synthetic`.
After the run, append a dated block to eval/results.md: top-1, top-3, blockers, gap recall, 3 worst cases.
