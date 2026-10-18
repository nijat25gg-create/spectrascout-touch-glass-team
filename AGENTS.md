# SpectraScout, Team Touch Glass (schubKI 2026, AFS challenge)

AI assistant for an Art Fiber Systems (AFS) expert: customer text in, first technical
assessment out (missing info, ranked in-line spectroscopy methods, rationale,
first feasibility experiment). The expert stays in charge. The jury is most likely AFS:
optimise for "transparent, easy to verify, easy to correct".

## Product pipeline (do not change the shape)
customer text → llm.extract (C2→C3: 16 parameters with quotes, 12 features, 34 attributes)
→ engine.score_methods (C4→C5, deterministic gates engine on rules/gates.yaml; C5.assessment = full result)
→ llm.explain (C6→C7) → briefing C8.
Recompute (C1b): expert edits an attribute or answers a question, step A is skipped.
The LLM never chooses the method. The PRODUCT is not a multi-agent system.
Subagents and workflows in .claude/ are developer tools only.

Overlays (allowed, they must not change the core): completeness %, number→class
conversion, OpenAlex literature (parallel to step B, 3 s timeout), Jev cross-check,
customer email template, rule trace in the UI.

## Source of truth
- contracts/models.py (Pydantic, SCHEMA_VERSION "0.2"). Change contracts only by
  ADDING optional fields. Never rename or remove. After any change run
  `python contracts/check_contracts.py`, `python contracts/export_schemas.py`
  and update contracts/examples.
- rules/gates.yaml (since 18.10 the only rules engine; rules/rules.yaml retired to legacy/):
  rule = {id, step, applies_to, targets, when, effect, on_unknown, because, source, tests}.
  `exclude` only for physical impossibility or a mandatory condition, always with an AFS source.
  Checks: `python rules/check_gates.py`, `python -m pytest -q engine/test_gates.py`, `python rules/mutate_gates.py`.

## Owners (touch other folders only via PR + message to the owner)
contracts/, llm/, kb/ → Nidzhat · backend/ → Semyon · frontend/ → Gadzhi
engine/, eval/, rules/, data/test-cases/ → Nikita + team

## Commands
- `python contracts/check_contracts.py`   contracts and examples are consistent
- `python -m engine.selftest`              engine sanity checks
- `LLM_MOCK=1 python -m llm.selftest`      LLM layer in mock mode
- `LLM_MOCK=1 python run_case.py`          full chain without an API key
- backend (from backend/): `uvicorn app.main:app --reload`, tests: `pytest`
  API: POST /assessments (C1 → C8), POST /assessments/recalculate (C1b or the posted briefing → C8)
- frontend (from frontend/): `npm install`, `npm run dev` (proxy /api → localhost:8000)
- Windows PowerShell: set mock with `$env:LLM_MOCK=1` before the command.
- macOS may need `python3` instead of `python`.

## Rules
- Secrets only in .env. Never read, print or commit .env or any key.
- Default to LLM_MOCK=1. Real API calls only when the user asks.
- Follow CONTRIBUTING.md: branch `<type>/<area>-<desc>`, commit `type(area): ...`,
  PR into main, squash merge, main must always run.
- Do not write into knowledge/, prompts/, cases/ (old template, being removed).
- Before pushing, `git diff main --stat` and check you did not touch other owners' files.
- Chemistry in rules and kb is a draft until Nikita confirms (status draft-unverified).
- Solution code is written from Fri 16.10 18:00. Anything prepared earlier goes
  into DECLARATIONS.md.
- Talk to the team in Russian. Code, comments, commits in English.
