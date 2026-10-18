# API costs

What one analysis costs in real API calls, and how to run SpectraScout without any cost.
Prices as listed on 18 October 2026 (USD per million tokens). Check the sources before budgeting:
prices change.

## Short answer

| | Typical analysis | Worst case (long text, retry) |
|---|---|---|
| Step A, extraction (Claude Haiku 5.5) | about $0.003 | about $0.01 |
| Step B, explanation (Claude Sonnet 5.5) | about $0.06 | about $0.20 |
| Jev cross-check (optional, OpenRouter) | $0.0002 (measured: $0.0001976 per run) | about $0.0005 |
| **Total per analysis** | **about $0.06** | **about $0.21** |

100 analyses cost about $6. With `LLM_MOCK=1` (the default) nothing is called and nothing is paid.

## Which calls one analysis makes

One click on **Analyze** runs this pipeline:

```
customer text → step A (LLM)  → rules engine (no LLM) → step B (LLM) → briefing
                 Jev (optional, parallel to step A's result, only if JEV_LIVE=1)
```

| Call | Model (default) | Set with | Calls per analysis |
|---|---|---|---|
| Step A: extract facts and attributes from the customer text | `claude-haiku-5-5` | `MODEL_EXTRACT` | 1 (a 2nd only if the answer was cut off, see Retries) |
| Rules engine: rank the methods | none, deterministic Python | — | 0 |
| Step B: explain the ranking, questions, experiment | `claude-sonnet-5-5` | `MODEL_REASON` | 1 (same retry rule) |
| Jev: cross-check how sure step A is about each attribute | `typesafe/jev-1.14` on OpenRouter | `JEV_LIVE=1`, `JEV_MODEL` | about 5 (34 attributes in batches of 8) |

The language model never chooses the method. That is done by the rules engine, which costs nothing.

## Prices used

| Model | Input | Output | Cache read | Source |
|---|---|---|---|---|
| Claude Haiku 5.5 (prompt up to 100,000 tokens) | $0.10 | $0.50 | $0.01 | [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Sonnet 5.5 | $2.00 | $10.00 | $0.10 | [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Jev 1.14 (OpenRouter) | $0.042 | free | — | [OpenRouter: jev 1.14](https://openrouter.ai/models/typesafe/jev-1.14) |

Our prompts stay far below 100,000 tokens, so the lower Haiku price applies.
The Batch API halves Claude prices, but the app answers live, so it does not use batches.

## Token estimate per call

Estimated from the prompt files (about 4 characters per token). Not measured on live calls.

| Call | Input tokens | Output tokens | Max output (`max_tokens`) |
|---|---|---|---|
| Step A | about 7,000 (system prompt with the fact catalog 25 kB, customer text, output schema) | 2,000–5,000 | 10,000 |
| Step B | about 10,000–15,000 (system prompt 6 kB, reasoning addendum 5 kB, compact method B view 8 kB, case data) | 2,000–4,000 | 9,000 |
| Jev, each of about 5 calls | about 1,000–2,000 (customer text, 8 questions with options) | billed at $0 | — |

## Cost per call

| Call | Typical | Worst case |
|---|---|---|
| Step A | 7,000 × $0.10/M + 4,000 × $0.50/M ≈ **$0.003** | one retry at 1.5× output: ≈ **$0.01** |
| Step B | 12,000 × $2/M + 3,000 × $10/M ≈ **$0.054** | 15,000 in + 9,000 out, plus one retry ≈ **$0.20** |
| Jev (all calls of one analysis) | **$0.0001976, measured on a live run** | ≈ **$0.0005** (longer text) |

## Retries

If a structured answer is cut off (`json_invalid`), the client asks once more with 1.5 times the output
limit. That call is billed in full. Retries are rare with the current limits, but they are where the
worst case comes from.

## Recalculate

Recalculate runs only the rules engine. It costs nothing. (It is hidden in the current interface;
answers to the questions go into the customer text and a new analysis.)

## How to keep costs at zero or low

- `LLM_MOCK=1` (default in `.env.example`): built-in examples, no API calls.
- `JEV_LIVE=0` (default): no OpenRouter calls.
- Cheaper step B: set `MODEL_REASON=claude-haiku-5-5`. Step B then costs well under one cent,
  the explanations are shorter and less careful.

## Keys

Keys are never in the repository. Copy `.env.example` to `.env` and replace `[API KEY needed]`:

```
ANTHROPIC_API_KEY=[API KEY needed]      # steps A and B
OPENROUTER_API_KEY=[API KEY needed]     # only for Jev (JEV_LIVE=1)
LLM_MOCK=0                              # 0 = real calls
```

`.env` is listed in `.gitignore`.
