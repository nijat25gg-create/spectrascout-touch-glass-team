---
name: integration-checker
description: Checks that backend responses and frontend rendering match C8 (v0.2 core plus optional v0.3 attributes/assessment) end to end. Use after changes in backend/ or frontend/ and before the 17:00 end-to-end run.
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
model: sonnet
color: orange
maxTurns: 30
---
1. Start the backend with LLM_MOCK=1 (see backend/README.md), wait for GET /health.
2. POST /assessments with contracts/examples/C1_analyze_request.example.json,
   POST /assessments/recalculate with C1b_recompute_request.example.json.
3. Validate both responses with contracts.models.Briefing (python one-liner).
4. Check frontend/render.js reads every C8 field: features, questions[].feature,
   methods.ranked[].scores (rule_id, note), methods.ranked[].claims, methods.rejected, changes.
   v0.3 optional: attributes[], assessment (decision_status, selected, premise_flags, questions, lab_checks),
   claims[].source, questions[].attribute. Missing in the UI is a finding, not an error, until Gadzhi adds them.
5. Stop the server.
Report missing or mismatched fields per file, in Russian. Do not edit files.
