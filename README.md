# SpectraScout

**AI assistant for in-line spectroscopy use-case assessment**

Team **Touch Glass** · schubKI National AI Hackathon 2026 · Challenge by Art Fiber Systems (AFS)

> Built during the hackathon (16–18 October 2026). Everything prepared beforehand, and every model,
> library, dataset and AI tool we use, is listed in [DECLARATIONS.md](DECLARATIONS.md).

## Summary

An AFS expert pastes a short customer request ("we want to follow the API content in our powder blend in-line").
SpectraScout returns a first technical assessment: which facts are known and which are missing,
a ranked list of in-line spectroscopy methods with the probe interface to test first, the reasons for and against each
one with the AFS source behind it, the questions that would change the ranking most, and a first feasibility
experiment. The LLM reads and explains; a deterministic rules engine ranks. Every number in the briefing can be
traced to a rule and a page in the AFS materials, and the expert can correct any fact and recalculate.

## The problem

Industrial customers usually know *what* they need to monitor: concentration, reaction progress, contamination,
moisture or product quality. They often don't know *which* spectroscopy method, spectral range, fiber probe or
measurement setup should be tested first. Today an AFS expert works this out by hand for every request.

## What the assistant does

1. Reads a short customer use case (English or German).
2. Extracts the facts of the case, each with a status: `reported` (with the customer's exact words), `inferred`, or
   `unknown`. Missing data stays visible as unknown; it is never filled with a default.
3. Ranks the five method families (NIR, MIR, Raman, UV-Vis, fluorescence) together with a sample interface
   (ATR probe, transflection, diffuse reflection, Raman probe, ...).
4. Explains the ranking from the method cards and the rule trace, and lists the decisive open questions.
5. Proposes a first feasibility experiment.

It does not replace the expert. It structures the first customer discussion and keeps every recommendation
transparent, easy to verify and easy to correct.

## Demo

| | |
|---|---|
| Demo video (English, max. 5 min) | _add link_ |
| Live app | _add link_ |
| Slides | _add link_ |

## How it works

```
customer text
  → LLM step A   extract facts with quotes (llm/extract.py)
  → engine       method B, deterministic (engine/b/, rules/b/)
  → LLM step B   rationale, questions, experiment, only from method cards and the rule trace (llm/explain.py)
  → briefing for the AFS expert (frontend/)
expert edits a fact or answers a question → recalculate (step A is skipped)
```

**The LLM never chooses the method.** Step A only reads the text; a quote that is not literally in the customer
text is discarded. Step B only explains; sources, claims and attributes it invents are removed by a check.

**Method B** (team spec *spectroscopy-rules 1.2-draft*) scores every method × sample-interface configuration in
four stages, each 0–9:

| Stage | Question |
|---|---|
| Q1 | Is the target observable and distinguishable in this matrix? |
| Q1b | Is the required performance achievable? |
| Q2 | Is there optical access with this interface? |
| Q3 | Is it compatible with the process (temperature, cleaning, fouling, reuse of existing assets)? |

Suitability = Q1 + Q1b + Q2 + Q3 (0–36). Q4 (0–3, evidence that the setup has been verified) only affects the
confidence. Each rule returns MATCH / MISMATCH / UNKNOWN / NOT_APPLICABLE; unknown facts give an interval instead of a
guess. A sensitivity pass tries every unknown fact over its domain: the facts that would change the leader become
the questions to the customer. Exclusions only come from a hard rule with a source and known facts.

**Method A** (gates engine, `rules/gates.yaml`) is the earlier engine. It still runs alongside for comparison.
**Jev** is an optional, independent cross-check of step A (`JEV_LIVE=1`). It can only lower the confidence of an
extracted value, never choose a method or add a fact.

How the decision is made: [docs/decision-method.md](docs/decision-method.md) (English),
[docs/decision-method.de.md](docs/decision-method.de.md) (Deutsch).

Details: [docs/method-b.md](docs/method-b.md), [docs/architecture.md](docs/architecture.md), data contracts in
[contracts/](contracts/README.md).
API costs per analysis: [docs/api-costs.md](docs/api-costs.md).

## Evaluation

| What | Result |
|---|---|
| Step A facts vs hand-labelled golden facts, development cases D01–D08 (live, 18.10) | 55 / 56 |
| Leading method is one the golden case expects, D01–D08 | 7 / 7 |
| Engine acceptance and invariant tests (`engine/test_gates.py`, `engine/b/test_b.py`) | 89 passed |
| Backend tests | 50 passed |

Test cases H01–H06 are frozen (`eval/h_frozen.sha256`) and used only for measurement, never for tuning prompts or
rules. The step A numbers are a single live run with `claude-haiku-5-5`; reports are in `eval/`. Reports contain no
customer text.

## Getting started

```bash
git clone https://github.com/nikgiblion/touch-glass-schubki.git
cd touch-glass-schubki
cp .env.example .env                  # LLM_MOCK=1 works without a key
pip install -r requirements.txt        # macOS: use pip3 and python3 in all commands below
python contracts/check_contracts.py   # contracts and examples consistent
LLM_MOCK=1 python run_case.py         # full chain on an example case, no key needed
```

Backend and expert screen:

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload   # API on :8000
cd frontend && npm install && npm run dev                                        # UI, proxies /api to :8000
```

Live mode: copy `.env.example` to `.env`, replace `[API KEY needed]` in `ANTHROPIC_API_KEY` with your key and set `LLM_MOCK=0` there. The key is never committed. Costs: [docs/api-costs.md](docs/api-costs.md).

| Switch | Values | Default |
|---|---|---|
| `ENGINE` | `b` method B ranks · `ab` method A ranks, B attached · `a` method A only | `b` |
| `B_RANK_MODE` | `technical` · `spec` (literal sort key of the spec) | `technical` |
| `EXTRACT_B` | `1` step A extracts method B facts directly · `0` bridge from method A attributes | `1` |
| `LLM_MOCK` | `1` canned example answers · `0` real Claude calls | `1` |
| `JEV_LIVE` | `1` Jev cross-check via OpenRouter · `0` off | `0` |

Checks:

```bash
python contracts/check_contracts.py
python -m engine.selftest
python -m pytest -q engine/test_gates.py engine/b/test_b.py
LLM_MOCK=1 python -m llm.selftest
cd backend && LLM_MOCK=1 pytest -q
LLM_MOCK=0 python -m eval.extract_b_eval --live   # needs the key, costs API calls
```

## Repository structure

| Folder | Owner | Content |
| --- | --- | --- |
| `contracts/` | Nidzhat | Data contracts C1–C8 (+C1b, E): Pydantic models, JSON Schemas, examples, checks |
| `llm/` | Nidzhat | Step A `extract()`, step B `explain()`, prompts, Jev client, `LLM_MOCK` |
| `engine/` | team | Method B engine (`engine/b/`), gates engine, scoring entry point `score_methods()` |
| `rules/` | Nikita | Method B catalog and rules (`rules/b/`), gates rules (`gates.yaml`), all with AFS page sources |
| `kb/` | Nikita, Nidzhat | Method cards used by step B |
| `eval/` | team | Golden facts, evaluation scripts and reports |
| `backend/` | Semyon | FastAPI service: `POST /assessments`, `POST /assessments/recalculate` |
| `frontend/` | Gadzhi | Expert screen: briefing, facts table, method cards, questions, PDF export |
| `data/test-cases/` | Nikita | Public test cases and the labelling template |
| `docs/` | all | Method B, architecture, demo script, submission checklist |
| `legacy/` | — | Retired points engine, reference only |

The AFS materials (`materials/`) are not in the repository. Rules cite them by document and page only.

## Limitations

- The chemistry in `rules/` and `kb/` is a draft until our domain expert has confirmed it (status `draft-unverified`).
- Rule effects and the score buckets are a first design (`design_v0_unvalidated`), not calibrated on measurements.
- Five method families and the 20 sample interfaces of the AFS catalog; combinations are shown as a hypothesis only.
- Evaluation is small: 8 development and 6 frozen test cases.

## Team Touch Glass

| Role | Name | GitHub |
|---|---|---|
| Domain expert, chemistry (PhD) | Nikita | @_username_ |
| Captain: product, LLM, pitch | Nidzhat | @_username_ |
| Backend and deployment | Semyon | @_username_ |
| Frontend and PDF export | Gadzhi | @_username_ |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branches, commits and pull requests.

## Declarations

All reused code, models, datasets, AI tools and pre-hackathon preparation are listed in [DECLARATIONS.md](DECLARATIONS.md).

## License

_TBD_
