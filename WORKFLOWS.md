# Dynamic workflows: for big parallel jobs (developer tool only)

A workflow = Claude writes a script that runs many subagents in parallel, you watch it in
`/workflows`. On Pro it must be switched on first: `/config` → Dynamic workflows.
On Pro the default size is "small" (fewer than 5 agents). Workflows burn usage limits
fast, so start on a small slice and never run them Saturday afternoon when we need limits
for real work.

Start one by writing "use a workflow" (or the keyword `ultracode`) in the prompt.
Save a good run as a command: `/workflows` → select → `s` → `.claude/workflows/`.

## Our 5 workflows

1. **Label the 20 test cases** (Fri evening)
   use a workflow: for every row in data/test-cases/internet-cases.csv one agent drafts
   expected_top_method, expected_rejected and the 3 most important missing parameters from
   kb/card-*.md and rules/rules.yaml; a second independent agent checks each draft;
   disagreements are marked NEEDS_NIKITA. Write data/test-cases/labels-draft.csv.

2. **Evidence for the 6 method cards** (Nikita or Nidzhat, Fri evening)
   use a workflow: one agent per kb/card-*.md, each finds 3–5 papers on OpenAlex for the
   card's main claims (in-line, fiber probes), cross-checks claims against the papers and
   writes kb/evidence/<method>.md as rows method | matrix | analyte | range | probe | result | limitation | DOI.
   Or: `/deep-research <question>` for one narrow question.

3. **AFS scenarios dry run** (Nidzhat, Sat morning, after we get the 8 AFS scenarios)
   use a workflow: run each AFS scenario through run_case.py with LLM_MOCK=0, then have
   afs-expert-critic judge each briefing independently; return one ranked list of the
   most common problems with owner.

4. **Pre-freeze audit** (Nidzhat, Sun 12:00, before the 16:00 feature freeze)
   use a workflow to review every file changed since the start of the hackathon for
   correctness bugs, contract mismatches and leaked secrets, adversarially verify each
   finding, then merge into one ranked list.

5. **Prompt A/B for step A** (Nidzhat, Sat)
   use a workflow: run both versions of llm/prompts/extract_system.md on all labelled
   cases, compare parameter accuracy and unknown-detection, report which wins per parameter.

Never use workflows inside the product. The product answers in seconds with two LLM calls.
