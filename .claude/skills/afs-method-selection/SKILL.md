---
name: afs-method-selection
description: Order of the AFS method decision in method B (spec spectroscopy-rules 1.2) - facts with status, Q1 signal, Q1b achievability, Q2 interface, Q3 process, Q4 evidence, scores 0-9, sensitivity of unknowns. Use when changing rules/b, engine/b, golden_b, or explaining why a method was chosen.
---

# AFS method selection (method B)

The deterministic engine `engine/b` on `rules/b/rules_b.yaml` + `rules/b/catalog_b.yaml` makes the choice
(spec `spectroscopy-rules` 1.2-draft, summary in `docs/method-b.md`).
The LLM never chooses the method: step A extracts facts, step B explains the finished trace.

## 1. Facts first
- Every property = value + unit/category + source + status: `reported` (client said it, with a quote),
  `inferred`, `unknown`, `confirmed_experiment`, `confirmed_expert`, `conflicting`.
- Not mentioned = `unknown`, never a default. "No fluorescence" (stated) differs from "fluorescence not mentioned".
- `inferred` never counts as covered and never raises confidence.

## 2. Unit of decision
- Case = one task × one sample/stream × one process point. Two targets or two streams = two Cases
  (fat and protein, whey and concentrate). Mandatory targets combine as min, not as average.
- Candidate = Method × SampleInterface (S01 Table 1 pairs) × Configuration concept (e.g. reuse existing link / new link).

## 3. Order of the questions (six properties of «Сущности v3»)
| Stage | Question | Property |
|---|---|---|
| Q1 | Does the method give a signal of this target, separable from the matrix? | observability, distinguishability |
| Q1b | Is the required concentration, error and speed achievable? (no profile in the materials → UNKNOWN, never invented) | achievability |
| Q2 | Can this interface get the signal from this sample (form, opacity, contact, representativity)? | optical access |
| Q3 | Does the configuration survive the process (temperature, fouling, distance, fiber window, reuse)? | process compatibility |
| Q4 | How strong and how close is the evidence (0-3)? Only confidence, never the score | verifiability |

## 4. Scoring
- Each rule: MATCH / MISMATCH / UNKNOWN / NOT_APPLICABLE with its effect. UNKNOWN adds 0 but keeps the possible effects (interval).
- Group sum capped to [-3, 3]; Score per stage 0-9 (bucket_10_v1_proposed); suitability = Q1+Q1b+Q2+Q3 (0-36).
- One cause counts once (exclusive groups: the most specific row wins).
- Score 0 is not an exclusion. Exclusion only by a hard rule with known facts and an AFS source, at the narrowest
  level: method, method × interface, or one configuration. An unsuitable existing cable excludes that assembly, not MIR.

## 5. Unknowns and questions
- Sensitivity: try each unknown over its allowed values. Changes the leading method or an exclusion → high;
  changes the top 3 → medium; else do not ask now. At most 3 questions, each with "why" (which answer changes what).
- Undefined target → `needs_target`: screening directions only, the first question is the target.
- Ranking mode is a team decision (`B_RANK_MODE`): spec puts `critical_unknown` first; technical keeps it as a marker.

## 6. Recommendation
- Show method, interface, configuration, scores with intervals, confidence, and the conditions under which it holds.
- First experiment: real client samples over the stated variation, independent reference, split by batch/run,
  each single method as a baseline, acceptance criteria agreed with the client (none invented).

## Do not
- Call a method "best" without a source and without conditions; a high score is not validation.
- Turn a qualitative rating (XLSX sensitivity/selectivity/cost) into a number or a guarantee.
- Present a published or in-vitro study as process or clinical readiness (R_Q4_07).
- Tune rules to the frozen test cases H01-H06. Calibrate on D01-D08 only.
