# Integration as an explain_system.md supplement

## Delivery boundary

Version 1.2.0 is a domain-reasoning addendum, not a replacement system prompt. No application checkout, actual explain_system.md, contracts or method B rubric was available in this workspace. Method B handling reflects the supplied field descriptions, not a verified runtime schema. No service code, rules, contracts or installed skill configuration changed; no real LLM/API calls were made.

The original chemistry skill contributes structure/property reasoning and analytical validation. The focused chemistry reference retains bonding, organic groups, environment effects and mixture interpretation. Unrelated synthesis tutorials remain outside scope.

## Precedence and assembly

Keep explain_system.md and its existing C7 contract authoritative. They own kb_card/source conventions, rule-ID prohibition, high risk handling and the 3–6 question count. The addendum describes how to reason within those fields; it supplies no new output schema. Preserve upstream assessment data internally without necessarily publishing its IDs, scores or traces.

The application caller explicitly selects method A or B and supplies the corresponding current assessment as delimited data. Method A uses C5.assessment and the existing pipeline unchanged. Method B uses assessment_b and the actual Q1–Q4 rubric, facts_b status definitions, critical_unknown semantics and Case relationships. The package introduces no classifier and does not transform one method into the other. If both assessment types are supplied, the caller must designate which controls the current explanation. Do not combine their results implicitly.

Append the generated supplement to the existing trusted explanation instructions. Keep customer text, assessments, quotes and retrieved evidence in data sections, not interpolated into governing instructions. Sources exposed to the briefing must already be permitted by the host prompt and its kb_card/source input. CH01–CH05 are background only and must never appear in briefing citations. Package locators are not new citation IDs.

## Exactly what goes into each call

The default runtime profile is **core only**: SKILL.md body plus the explicit method designation. All reference files, source registers, integration notes, evaluation cases and original publications are omitted. The script strips YAML discovery metadata. Relative links in the body are authoring pointers; they do not fetch files during an API call.

Optional selection is the caller's responsibility before the call. No LLM router or second product agent is added. Until the application has explicit selection logic, use core only; do not silently send the whole package.

| Explicit include flag | Caller condition | Added content |
|---|---|---|
| chemistry | A known chemical composition/group or suspected environment effect needs chemical explanation | chemistry-foundations.md |
| domain | An optical chain, probe, interface or instrumentation constraint needs detailed checking | domain-checks.md |
| experiment | The request needs a detailed validation or comparison protocol beyond the core plan | experiment-design.md |

These are caller configuration decisions, not claims that a router is already integrated. If the application cannot determine a condition, leave the optional flag off. The core remains usable. The present assembler includes a complete selected reference; it does not claim automatic section extraction. If several references are routinely requested, inspect actual token count and latency before choosing a production budget. No tokenizer-based budget is asserted here.

Generate the addendum from the project/workspace root, for example:

```powershell
python outputs/spectrascout-reasoning/scripts/build_context.py --method b --output tmp/reasoning-b-core.txt
python outputs/spectrascout-reasoning/scripts/build_context.py --method a --include chemistry --include domain --output tmp/reasoning-a-optics.txt
```

The output contains only the addendum. Append it to the existing explain_system.md in the application's prompt assembly, then pass the current input data. The helper neither reads the host prompt nor calls any API, and refuses to overwrite an existing output or write generated prompts into the skill package. Do not load the old chemist-analyst instructions alongside this supplement.

The existing OpenAlex overlay remains parallel to step B with its 3 s timeout. Unavailable retrieval is not negative evidence. Jev and the UI trace remain overlays. Do not include evaluation enquiries in prompts, retrieval indexes or training examples.

## Checks after repository access

Read the actual host prompt, contract and selected assessment example. For B, inspect rubric and status definitions before claiming numerical interpretation. Verify C7 against its existing contract, source references against supplied kb_card/source data, no rule-ID leakage, question count and risk behavior. Check each Case retains its own facts/unknowns, and no score is converted into a probability or new rank. For A, check order, eligibility and recompute provenance against the unchanged engine result.

Use LLM_MOCK=1 by default. Mock mode checks wiring and contracts, not scientific explanation quality. Domain review by Nikita and actual runtime verification remain outstanding. Follow ownership/PR requirements for any later service integration. Contract/rule changes are not required by this package; if separately authorized, run their prescribed checks.
