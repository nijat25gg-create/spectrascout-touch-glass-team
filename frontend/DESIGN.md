# Frontend design (CS 4)

Status: agreed 2026-10-14. Owner: Gadzhi.

## Goal

One page where an AFS expert understands the recommendation in a minute and can correct it.
Done when a real AFS case goes "paste text -> 8 blocks -> answer a question -> PDF" without errors.

## Decisions

- Stack: plain HTML + CSS + JavaScript (ES modules). Locally, Vite on port 5173 serves the page and proxies `/api` to FastAPI. In production one origin serves the page and forwards `/api` the same way (`deploy/nginx.conf`).
- Contract: agreed with Semyon on 2026-10-14: the backend returns the briefing from `docs/briefing.schema.json` v0.1 (branch cs1). The screen also accepts the Hub version v0.2 (`claims`, `features`). The page calls `POST /api/assessments` with `{text, language}`; the proxy strips `/api` and FastAPI serves `POST /assessments`. `POST /api/assessments/recalculate` sends the whole briefing with `questions[].answer` and edited `parameters` (`source: "expert_edit"`) and expects a new briefing with `meta.recomputed: true`. Errors: `{"detail": ...}` (FastAPI) or `{"error": {"code", "message"}}`.
- UI language: DE | EN switch in the top bar (remembered in the browser). After an analysis the UI switches to the case language once; the expert can switch back. It changes block titles, buttons, parameter and feature names and the PDF. Briefing texts stay in the language the backend wrote them in. The form select is the language of the customer text, sent in C1.
- The frontend never computes scores. It only shows the briefing and sends edits/answers.
- Method B (18.10 evening, branch feat/gates-engine-v03; C8 `assessment_b` + `facts_b`, contracts v0.4): when `assessment_b.cases` is present the method B screen is the main one and the method A blocks are hidden (`#result.engine-b`). Per Case (tabs when the request splits, plus the `aggregate_bundle` line): decision status and the engine `headline`, the leading method and up to two reasons (its most specific matching factors with note and source) → premises → method cards (suitability of 36 with interval, Q1/Q1b/Q2/Q3 0–9, Q4 0–3, confidence, "critical question open"; first three, the rest folded) → questions (high/medium, why folded) → ruled out (folded) → decision path by factors per stage (folded) → method A result for comparison (folded). The parameters tab holds the `facts_b` table (value · unit · status in colour, customer's words on hover, unknown visible); editing a fact sets `confirmed_expert` and "recalculate" posts the briefing with `facts_b`. Without `assessment_b` the MVP screen below is shown unchanged.
- Screen order (team, 18.10 evening, checked against skill `afs-answer-and-feasibility`, which allows any clear format): decision status + client premises + one summary line → recommended methods (selected gates rows only), each card with "why it fits" (the engine rules that supported the row, text from `rules/gates.yaml` via `vocab.json`, with source, plus step B claims once per method) and "still to check" (its risks and open points) → key unknowns line (section 1 of the AFS answer; from C7 requirements, else stated attributes and the attributes the method questions ask for) → questions (deciding ones with answer lists, plan questions as one compact list) with Recalculate / Copy / PDF under them → check on samples → other options (folded: other rows and ruled-out ones; no block when there are none) → concept, range, risks, plan → decision path (folded) → parameters and attributes (folded tab, its open state is remembered). No method can be justified (`selected` empty): the questions move above the methods. Data the backend does not send is not drawn. Print opens every folded block.
- Layout follows the AFS answer structure (Examples, section 3): decision status, requirements (stated / key unknowns), clarification questions, recommendation and ruled-out methods, measurement concept, spectral range, risks, feasibility plan with decision basis, sources.
- `adapt.js` translates any briefing (v0.1, v0.2, draft v0.3 from plan v4: `decision_status`, `assessment` = C5, `reasoning` = C7, `meta.completeness`) into one view; `render.js` only reads that view. When the final v0.3 arrives, only `adapt.js` changes. Missing fields hide their block.
- Matrix "six relations × candidates" (docs/decision-model.md): observability, separability, achievability, optical access, process compatibility, verifiability; cells fit / part / no / block / ?. Read from `assessment.scores[].relations` and `assessment.excluded[].relations` (draft). Ruled-out candidates are listed last.
- Fake mode, demo case without its own test briefing: a note says the old v0.2 example is shown.
- "What changed" after recalculation is computed on the frontend (`diffViews` in `adapt.js`): new top method, category or score up/down, newly ruled out, status, completeness.
- Fake mode: `USE_FAKE` in `config.js`, or open the page with `?fake`. Demo buttons D01–D08 and H01–H06 carry the AFS texts; D01 and H04 show `fake-d01.json`, `fake-h04.json` (gates engine output, see below), typed text shows `fake-briefing.json` (v0.2).
- Gates engine (18.10, `engine/gates.py`, contracts v0.3 `GatesAssessment` in C5/C8 `assessment`, `attributes` in C8). Recognised by `assessment.rows`; laid over the v0.2 body. The engine gives: decision status, client premises (contradicted / not supported), catalog rows K01–K10 (candidate / needs info / ruled out, AFS evidence level, risks), questions (required, impact = share of answers that change the decision), lab checks (step 0, never asked to the client) and the trace, drawn as the decision path Q1 → Q4. Selected rows are full cards, the other rows one line each. `assessment = null` (engine failed) hides these blocks. If the `rules.yaml` ranking (v0.2 `methods`) picks another first method, the decision box says so and the points ranking is listed for comparison: the team has not chosen which engine leads C8.
- Gates view, 18.10 noon (Nidzhat's reply): `selected` empty (insufficient / outside scope) shows "no method can be justified yet" instead of an empty block; `assessment.ignored_inputs` shows a warning in the decision box; every question with a vocabulary attribute (engine or step B `questions[].attribute`) gets the answer list; step B `claims[]` of the same method appear on the row card with `claims[].source` as a chip (`kb_card = "afs-source"` hides the card name); the 12 v0.2 features are hidden when `attributes` are present; unknown attributes are folded under the table.
- AFS material stays local (before the repo goes public): `cases.js` keeps only id and title of D01–D08 and H01–H06; the texts and the D01/H04 test briefings live in `cases.local.js`, `fake-d01.json`, `fake-h04.json`, all git-ignored (template `cases.local.example.js`). `app.js` loads `cases.local.js` if it exists; without it a D/H button leaves the box empty with a hint. The S row (team material) stays in the repository.
- Demo row S: `fake-s02.json`, `fake-s04.json`, `fake-moisture.json` are C8 v0.3 briefings from Nidzhat (synthetic team cases S02/S04 and the contracts example, step B texts simulated). The button text is the briefing summary (the customer texts are not in the briefing).
- Answering a gates question: a list of the attribute's values (`vocab.json`, copy of `rules/gates.yaml`) writes `briefing.attributes[name] = {value, status: "known", quote: null}`; the backend reruns the engine on "recalculate". In fake mode the test file carries the real engine output per single answer (`_fake_whatif`), made by `tools/make_gates_fakes.py` from the golden attributes (written by hand, not a live extraction).

## Files

| File | Job |
|---|---|
| `index.html` | layout: input, 8 blocks, sticky actions |
| `style.css` | look + `@media print` for the PDF |
| `config.js` | `BASE_URL`, paths, `USE_FAKE` |
| `i18n.js` | DE/EN labels |
| `features.js` | DE/EN names of the 12 features (v0.2 only) |
| `fake-briefing.json` | copy of `docs/briefing.example.json` (cs1, v0.1) for fake mode |
| `fake-d01.json`, `fake-h04.json` | LOCAL, git-ignored: gates engine output on the golden attributes + placeholder C7 texts |
| `cases.local.js` | LOCAL, git-ignored: texts of the AFS cases D01–D08, H01–H06 (template `cases.local.example.js`) |
| `vocab.json` | attribute values for the answer lists and rule texts (`because`, `source`) for the method cards, generated from `rules/gates.yaml` by `tools/make_vocab.py` |
| `fake-s02.json`, `fake-s04.json`, `fake-moisture.json` | C8 v0.3 example briefings (Nidzhat, 18.10) |
| `tools/make_gates_fakes.py` | rebuilds the two fakes and `vocab.json` from the engine |
| `api.js` | `analyze()`, `recompute()`, error text from the backend |
| `render.js` | draws the 8 blocks from a briefing (display only) |
| `app.js` | state (`current`, `dirty`, UI language), buttons, edits, loading |

Rules: one state `current`; URLs only in `config.js`; text from the briefing only via `textContent` / `esc()`.

## Screen

1. Summary.
2. Parameters: 16 rows (value, status colour, customer quote), status counts. The expert can correct a value in place; the row becomes "known" and "edited". The 12 features are shown only if the briefing has them (v0.2).
3. Questions, high -> low, with `why` and a text box for the customer's answer (`questions[].answer`, printed in the PDF).
4. Ranked methods: score, mode, range, fiber, probe, confidence, bars per criterion with note and `rule_id`, claims with `kb_card`.
5. Rejected methods: reason, `rule_id`, "hard rule" vs "low score" (`blocker`).
6. Experiment. 7. Risks with severity. 8. Expert flags; a flag marks its target row with a flag icon, click scrolls to it.

Blocks 4 and 5 sit side by side and are the largest on screen.

## Schedule

- Wed: screen from `fake-briefing.json`, no backend.
- Thu: edits and answers, "Neu berechnen" sends the briefing to `/api/assessments/recalculate` (done early, Wednesday).
- Sat: highlight what changed after recompute (before/after diff on the frontend); PDF in DE and EN.
- Sun: screen for the video by 16:00 (H8).

## Open questions (CS 1)

- Error format of Semyon's backend (`detail` or `error`): both are supported.
- If the team moves the frontend to v0.2 later: `features`, `changes` and the C1b format come from `contracts/` (not on GitHub yet).
