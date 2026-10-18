# Prompts

Owner: captain (CS 1). Prompts live in files here, not inline in code, so everyone can review them.

| File | Step | What it does |
|---|---|---|
| `extract_system.md` | A | Customer text → 16 parameters (known / assumed / unknown, with a quote) and 12 features |
| `explain_system.md` | B | Engine result → rationale from method cards, follow-up questions, first feasibility experiment, risks |

Code: `llm/extract.py`, `llm/explain.py`. Output formats: contracts C3 and C7 in `contracts/models.py`.
