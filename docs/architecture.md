# Architecture (draft)

> Draft from team planning. Update after kickoff.

## Pipeline

```mermaid
flowchart TD
  A["Customer use case<br/>3–5 sentences, EN or DE"] --> B["Parameter extraction<br/>known / assumed / unknown + source quote"]
  B --> Q["Questions for the customer<br/>ranked by impact on the recommendation"]
  B --> M["Decision matrix<br/>methods × criteria, scores, blockers"]
  K[("Method cards<br/>UV-Vis, NIR, MIR, Raman, ...")] --> M
  R[("Rules and weights<br/>condition → effect on score")] --> M
  M --> T["Top 1–3 methods<br/>probe, mode, confidence"]
  M --> X["Rejected methods<br/>with a specific reason"]
  T --> J["Rationale<br/>with references to method cards"]
  T --> E["First feasibility experiment<br/>samples, reference, success criterion"]
  T --> RK["Risks and assumptions<br/>flagged when confidence is low"]
  Q --> UI["Expert briefing in the UI"]
  J --> UI
  X --> UI
  E --> UI
  RK --> UI
  UI -->|"expert edits a parameter<br/>or answers a question"| B
  UI --> P["PDF or email to the customer"]
```

## Design principles

- **Code scores, the LLM explains.** Method scores come from rules written by our chemist, so the same input always gives the same recommendation and the expert can see why each method got its score. The LLM reads the customer text and explains the finished result.
- **Rejected methods stay visible.** An AFS expert first checks whether something was dropped by mistake. Every rejected method shows a specific reason.
- **Recalculate on new information.** The first customer conversation is mostly clarification. Answering a question or editing a parameter updates the recommendation and shows what changed.

## Ownership

| Part | Folder | Owner |
|---|---|---|
| Prompts: parameter extraction, questions, rationale, experiment | `llm/prompts/` | Captain |
| API connecting all steps, deployment | `backend/` | Backend |
| Decision matrix, scoring, rejected methods, risks | `engine/` | Rules engine |
| Method cards / rules and weights | `kb/` / `rules/` | Chemist, rules engine |
| Test cases with expected answers | `data/test-cases/` | Chemist |
| Briefing UI, parameter editing, PDF export | `frontend/` | Frontend |
| Evaluation on test cases | `eval/` | Rules engine |
