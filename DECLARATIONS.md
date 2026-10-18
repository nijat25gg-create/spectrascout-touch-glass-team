# Declarations

The hackathon rules require us to disclose everything that was not built during the hackathon, plus all AI tools,
models, datasets and third-party code we use. Solution code was written from Friday 16.10.2026, 18:00.

## Prepared before the hackathon

| What | Date | Who | Notes |
|---|---|---|---|
| Repository template (structure, README, contributing guide, issue and PR templates) | 2026-10-12 | _name_ | Drafted with Claude (Anthropic). Contains no solution code. |
| Data contracts C1–C8, C1b, E (`contracts/`): Pydantic models, JSON Schemas, examples, checks | 2026-10-11 to 13 | Nidzhat | Drafted with Claude. Interfaces only, no solution logic. Extended during the hackathon (v0.3, v0.4 fields). |
| Team hub and onboarding (`docs/team-hub.html`, `docs/ONBOARDING.md`) | 2026-10-11 to 14 | Nidzhat | Planning documents, drafted with Claude |
| Background research (`docs/research-2026-10-14.md`) | 2026-10-14 | Nidzhat | Public sources, drafted with Claude |
| LLM module skeleton with mock mode (`llm/`) | 2026-10-14 | Nidzhat | Prompt for step A, step B draft. Drafted with Claude |
| Rules engine draft (`engine/score.py`), draft rules (`rules/rules.yaml`), end-to-end runner `run_case.py` | 2026-10-15 | Nidzhat | Drafted with Claude. The points engine and `rules.yaml` were retired during the hackathon (now in `legacy/`) |
| Knowledge base: method cards (`kb/card-*.md`, drafts) | 2026-10-14 | Nidzhat, Nikita | General knowledge, checked against the AFS materials during the hackathon |
| Test case template and labelling process (`data/test-cases/`) | 2026-10-11 to 13 | Nidzhat | Template only |
| Backend integration on the shared contracts (backend imports `contracts.models`, adapters to `llm/` and `engine/`, contract error codes) and number → class conversion `engine/numeric.py` | 2026-10-16 | Semyon, Nidzhat | Semyon's backend structure; integration drafted with Claude before the start |
| Developer tooling: Claude Code and Codex config (`AGENTS.md`, `CLAUDE.md`, `.claude/` subagents, skills, hooks) | 2026-10-16 | Nidzhat | Drafted with Claude. Developer tools only, not part of the product |
| Expert screen (`frontend/`): briefing view for C8 v0.1 and v0.2, DE/EN interface, loading and error states, parameter edits with units, answers, recompute call, print to PDF, fake mode with `fake-briefing.json` | 2026-10-13 to 15 | Gadzhi | Drafted with Claude. Plain HTML, CSS and JS |
| Vite dev server and `/api` proxy for the frontend (`frontend/package.json`, `frontend/vite.config.js`) | 2026-10-16 | Semyon | Dev setup only, no solution logic |
| 20 public test cases, full + gaps (`data/test-cases/internet-cases.csv`, c09–c28) | 2026-10-14 to 15 | Gadzhi | Built from public vendor application notes, links in `source_ref`. Researched and written with Claude. Not checked by a chemist |

## Built during the hackathon (16–18.10)

Gates engine (`rules/gates.yaml`, `engine/gates.py`), method B spec *spectroscopy-rules 1.2-draft* and its engine
(`rules/b/`, `engine/b/`), step A facts for method B, step B explanation check, Jev cross-check integration,
golden facts and evaluation (`eval/`), backend API and recalculation, expert screen for method B.

## AI tools used during development

| Tool | Used for |
|---|---|
| Claude (Anthropic, claude.ai) | Repository template, contracts, planning, research, drafting documents |
| Claude Code (Anthropic) | Coding assistant for all parts; subagents for checks and reviews. Commits written with it carry a `Co-Authored-By: Claude` line |

## Models and APIs used in the product

| Model / API | Provider | Used for | Default |
|---|---|---|---|
| `claude-haiku-5-5` (Claude API) | Anthropic | Step A: reading the customer text, facts with quotes | `MODEL_EXTRACT` |
| `claude-sonnet-5-5` (Claude API) | Anthropic | Step B: rationale, questions, feasibility experiment | `MODEL_REASON` |
| `typesafe/jev-1.14` via OpenRouter | OpenRouter | Optional independent cross-check of step A; lowers confidence only | off (`JEV_LIVE=0`) |

The method ranking itself uses no model: it is the deterministic rules engine.

## Third-party code and libraries

| Name | License | Used for | Link |
|---|---|---|---|
| anthropic (Python SDK) | MIT | Claude API calls | https://github.com/anthropics/anthropic-sdk-python |
| Pydantic, pydantic-settings | MIT | Data contracts, settings | https://docs.pydantic.dev |
| jsonschema | MIT | Contract checks | https://github.com/python-jsonschema/jsonschema |
| PyYAML | MIT | Rules and catalog files | https://pyyaml.org |
| FastAPI | MIT | Backend API | https://fastapi.tiangolo.com |
| Uvicorn | BSD-3-Clause | ASGI server | https://www.uvicorn.org |
| HTTPX | BSD-3-Clause | Backend tests | https://www.python-httpx.org |
| pytest | MIT | Tests | https://pytest.org |
| Vite | MIT | Frontend dev server and `/api` proxy (dev only) | https://vite.dev |
| nginx | BSD-2-Clause | Serving frontend and API in deployment (`deploy/nginx.conf`) | https://nginx.org |

## Datasets and customer data

| Source | Permission | Used for |
|---|---|---|
| AFS materials and customer use cases (D01–D08, H01–H06) | Provided by AFS for the hackathon | Rule sources (cited by document and page), testing and demo. Not in the repository (`materials/` is git-ignored); reports contain no customer text |
| Public vendor application notes (c09–c28) | Public web pages, linked in `source_ref` | Additional test cases |
