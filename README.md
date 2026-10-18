# How a Spectroscopic Analysis Method Is Selected

The customer describes their business problem, material, and process conditions. The system turns the request into structured facts, compares spectroscopic measurement options, and produces a preliminary recommendation: suitable methods and sample interfaces, a configuration concept, the reasons for the recommendation, significant unknowns, and an initial experiment. An expert confirms the final technical assessment.

The system provides the expert with the information needed to select a suitable spectroscopic analysis method and identify follow-up questions for the customer. The assessment considers the measurement task, sample properties, and actual process conditions. A method name alone does not determine accuracy, detection limit, or the suitability of an installation.

## The Decision Approach

The algorithm evaluates specific candidates against individual factors. Each factor compares a request attribute with a property of the method, sample interface, or assembly: for example, sample transparency against measurement geometry, target concentration against demonstrated sensitivity, or operating temperature against a component rating.

```text
Customer text and clarifications
  → extract facts with supporting quotes
  → task × sample × process conditions
  → assess methods and method–interface pairs
  → Configuration concepts
  → suitability + separate confidence assessment
  → follow-up questions and an experiment
```

`MeasurementTask`, `Sample`, and `ProcessContext` describe a specific case. `Method` and `SampleInterface` are shared catalogs with versioned properties, relationships, and constraints, compiled from spreadsheets, PDF files, and DOCX files and reviewed by an expert. They are reused across customers; the applicability of each property depends on the sample and conditions.

`Configuration` is constructed for the case from permitted combinations and contains one or more `MeasurementChannel` records. The catalog does not need to enumerate every possible assembly in advance. The measurement concept is established first, followed by component selection. `SuitabilityEvidence` stores sources and verification results together with their scope of applicability.

Each fact retains its value, unit or category, source quote, and status: explicitly reported, inferred, confirmed, unknown, or conflicting. Missing information does not become a negative answer.

An LLM extracts free text and supporting quotes. JEV can verify categories and individual semantic claims. The rule engine computes numerical comparisons, constraints, factor weights, transitions, and the final ranking. JEV provides typed judgments and verification; the final decision is not delegated to a standalone “choose the best method” question.

This decomposition follows the TypeSafe approach: assess individual claims and combine the results in code. Within a single call, questions share the same `state` but do not see one another’s answers. If a later stage needs an earlier result, the code updates the state first. This does not establish statistical independence between the events being assessed. [TypeSafe Introduction](https://docs.typesafe.ai/introduction)

## Questions Answered at Each Stage

| Stage | Question | What is compared | Tool and metric | Output used by the next step |
|---|---|---|---|---|
| Extraction | What must be measured, and what is known about the sample and process? | Customer text and clarifications → MeasurementTask, Sample, ProcessContext | LLM: facts and quotes. When verification is enabled: **JEV Choice** — a category question, returning a category and probability distribution; **JEV Noul** — a question about whether an individual claim is true, returning a probability of “yes” from 0 to 1 | A specific Case and a list of unknowns |
| Q1 | Can the method produce a distinguishable signal for the target property? | target, matrix, components, and optical properties ↔ observable_properties, signal_prerequisites, interferences | Rule predicates; where needed, **JEV Noul** verifies an individual claim about the target–signal relationship or an interference, returning a probability of “yes” from 0 to 1. Code calculates a score from 0 to 9 | Candidate methods, interference risks, and calibration risks |
| Q1b | Can the concentration, error, and timing requirements be met? | Customer requirements ↔ applicable LOD/LOQ, error, and total latency profiles | Numerical comparisons in code; where needed, **JEV Choice** assesses attainability from the supplied evidence, returning “attainable / conditional / unattainable / unknown” and a probability distribution. Code calculates a score from 0 to 9 | An assessment of requirements and checks that remain unconfirmed |
| Q2 | Can the interface obtain a representative signal from this sample? | phase, form, opacity, heterogeneity, and spatial_scope ↔ geometry, contact, sample_region, path/depth | Compatibility and optical access rules; score from 0 to 9 | Permitted Method × SampleInterface pairs and Configuration concepts |
| Q3 | Can the configuration operate in the customer’s process? | Temperature, pressure, environment, distance, resources, and constraints ↔ concept/component properties | Rules for classes of conditions first, followed by checks against component ratings; score from 0 to 9 | An assembly assessment and its stage of development |
| Q4 | How well is suitability supported for this target, sample, and set of conditions? | SuitabilityEvidence ↔ Case and Configuration | Evidence matching rules; evidence score from 0 to 3 and a separate project confidence assessment | A confidence label, limitations on transferring evidence, and an initial experiment |

The rule engine calculates the stage scores from 0 to 9. These are internal `stage_score` values. They differ from a **JEV Score** response, which represents the expected position on a defined scale and may be fractional. Formulas for all three JEV formats appear below.

### General Decision Criteria

1. **Observability — Q1:** Is the target property related to the signal produced by this method? Is the relationship direct, or will it require indirect calibration?
2. **Discriminability — Q1:** Can the useful signal be separated from the matrix, background, and other components?
3. **Optical access — Q2:** Can light reach the relevant part of the sample and return a sufficient signal with the selected geometry?
4. **Process compatibility — Q3:** Can the probe and components withstand the temperature, pressure, chemical environment, and installation conditions?
5. **Attainability of requirements — Q1b:** Is there a basis for expecting the required accuracy, detection limit, and measurement speed?
6. **Verifiability — Q4:** Are representative samples and an independent reference available to confirm the result?

The completeness of these checks depends on the rules and catalog content and is assessed using expert-reviewed cases.

**Algorithm calibration status.** Calibration of factor weights, thresholds, JEV rubrics, and confidence rules against expert-assessed cases is planned to improve recommendation accuracy. It has not yet been completed. The settings below are therefore initial parameters; their recommendation accuracy has not yet been established. Algorithm calibration and analytical calibration of a spectroscopic measurement are separate procedures.

## JEV Formulas from the TypeSafe Documentation

This section describes the mathematics of JEV primitives. The project-specific suitability and Q4 formulas are described separately below; TypeSafe does not define them.

### Noul — Probability of a Claim

For a state $x$ and a single claim $A$:

$$
p = P(A=\mathrm{true}\mid x), \qquad p\in[0,1].
$$

The `noul` response is the probability of “yes.” The application selects thresholds $\tau_-<\tau_+$:

$$
\operatorname{decision}(p)=
\begin{cases}
\mathrm{yes}, & p\ge\tau_+,\\
\mathrm{no}, & p\le\tau_-,\\
\mathrm{unknown/review}, & \tau_-<p<\tau_+.
\end{cases}
$$

This threshold policy belongs to the application. Thresholds depend on the consequences of errors and must be validated on the application’s own data. An unknown fact cannot be treated as established solely because of a model response. [TypeSafe Noul](https://docs.typesafe.ai/primitives/noul)

### Choice — Category Selection

For $n$ options, JEV returns a distribution and a selected option:

$$
p_i=P(Y=i\mid x),\qquad \sum_{i=1}^{n}p_i=1,
\qquad \hat y=\underset{i}{\operatorname{argmax}}\;p_i.
$$

Examples include classifying transparency, phase, or target type. Where the list may be incomplete, it includes an `unknown`/`other` category. [TypeSafe Choice](https://docs.typesafe.ai/primitives/choice)

### Score — Expected Position on a Scale

For $n$ described levels indexed $0,\ldots,n-1$:

$$
s_{\mathrm{JEV}}=\sum_{i=0}^{n-1}i\,p_i.
$$

For ten levels:

$$
s_{\mathrm{JEV}}=\sum_{i=0}^{9}i\,p_i\in[0,9].
$$

The result may be fractional. For example, $p_7=0.2$, $p_8=0.6$, and $p_9=0.2$ give $s=8$. This is a position under the defined rubric, not a measured concentration or a probability of successful deployment. [TypeSafe Score](https://docs.typesafe.ai/primitives/score)

### Primitive Confidence

The following formulas are published in [TypeSafe Confidence](https://docs.typesafe.ai/confidence#how-confidence-is-calculated).

Noul does not return a separate confidence field. The documentation suggests computing the following if needed:

$$
C_{\mathrm{Noul}}=|2p-1|.
$$

For Choice, with $n\ge2$ and $p_{\max}=\max_i p_i$:

$$
C_{\mathrm{Choice}}=
\frac{p_{\max}-\frac1n}{1-\frac1n}.
$$

For Score, where $m=\operatorname{argmax}_i p_i$:

$$
D_{\mathrm{unif}}=
\frac1n\sum_{i=0}^{n-1}\left|i-\frac{n-1}{2}\right|,
$$

$$
C_{\mathrm{Score}}=
\max\left(0,\;1-
\frac{\sum_{i=0}^{n-1}p_i|i-m|}{D_{\mathrm{unif}}}
\right).
$$

For $n=10$, $D_{\mathrm{unif}}=2.5$. In the example distribution above, $m=8$, so:

$$
C_{\mathrm{Score}}=
1-\frac{0.2\cdot1+0.6\cdot0+0.2\cdot1}{2.5}=0.84.
$$

This characterizes the certainty of the model’s response. It does not establish the quality of a physical experiment.

### API Contract Clarification

In the official HTTP API, the number of Score levels is defined by the length of the ordered `criteria` array: ten descriptions define levels 0–9. The `levels: 10` field in the project contract may be a setting of our adapter; it should not automatically be treated as a TypeSafe request field. The native `score` has a numeric type and allows fractional values. [TypeSafe API reference](https://docs.typesafe.ai/api)

The integer stage score and fractional JEV response are therefore stored separately as `stage_score` and `jev_score`, together with `probabilities`, `confidence`, and the rubric version. Rejecting fractional values is appropriate for an internal `stage_score`, but not for the original `jev_score`.

## How the Algorithm Calculates Its Metrics

The formulas below define the project’s ranking model. Its weights, group caps, and thresholds require calibration against expert-reviewed cases; they are not TypeSafe formulas.

### Factors and Stage Scores

For a factor $f$ and candidate $c$, a rule returns a contribution:

$$
e_f(c)=
\begin{cases}
+k_f, & \text{a match is confirmed},\\
-k_f, & \text{a soft risk or mismatch is established},\\
0, & \text{the outcome is neutral, unknown, or not applicable}.
\end{cases}
$$

The last three states remain distinct in the rule trace. For UNKNOWN, the range of possible contributions is retained; a numerical zero does not establish a match. A hard exclusion is recorded as a separate flag.

Each technical stage has four factor groups. In the initial model:

$$
r_g(c)=\operatorname{clip}\left(\sum_{f\in g}e_f(c),-3,3\right),
\qquad r_q(c)=\sum_{g=1}^{4}r_g(c)\in[-12,12].
$$

Factors that repeat the same underlying cause are counted once, according to the mutually exclusive group rules. The stage score is:

$$
q_q(c)=B_q\bigl(r_q(c)\bigr)\in\{0,1,\ldots,9\}.
$$

Under the proposed bucket thresholds, which have not yet been approved:

$$
B_q(r)=\sum_{t\in\{-5,-3,-1,0,1,2,3,4,6\}}\mathbf1\{r\ge t\}.
$$

This quantizes **weighted factor contributions**. It does not replace the JEV expected-value formula or require JEV to repeat the arithmetic.

### Suitability and Exclusions

For a candidate without a confirmed disqualification:

$$
S(c)=q_{Q1}(c)+q_{Q1b}(c)+q_{Q2}(c)+q_{Q3}(c)\in[0,36],
$$

$$
S_{\%}(c)=100\frac{S(c)}{36}.
$$

The percentage is a relative suitability index. If physical incompatibility is established, the candidate is excluded regardless of its total score. The exclusion scope is limited by the evidence: a method for the Case, a method–interface pair, or a specific assembly. A low score alone does not imply EXCLUDE.

### Q4 and Recommendation Confidence

The evidence score $E(c)=q_{Q4}(c)\in\{0,1,2,3\}$ represents the progression from no relevant data to a comparable independent verification. Evidence strength is stored together with its positive or negative result.

Let $F_c$ be the set of relevant, applicable technical factors, excluding purely diagnostic factors. Then:

$$
\operatorname{coverage}(c)=
\frac{\#\{f\in F_c:\text{inputs explicit/confirmed, supporting basis verified}\}}
{|F_c|}.
$$

If $F_c$ is empty, coverage is unknown. The project’s initial policy is:

$$
C_{\mathrm{recommendation}}(c)=
\begin{cases}
\mathrm{high}, & E\ge2,\ coverage\ge0.80,\ \text{no critical unknowns},\\
\mathrm{medium}, & E\ge1,\ coverage\ge0.50,\ \text{no source conflicts},\\
\mathrm{low}, & \text{otherwise}.
\end{cases}
$$

The first matching branch applies. This is **project-specific confidence**, distinct from JEV’s $C_{\mathrm{Choice}}$ and $C_{\mathrm{Score}}$. Q4 is not included in $S(c)$, and high model confidence does not replace a relevant experiment.

### Ranking and Active Questioning

The code removes disqualified candidates, flags candidates with critical unknowns, and then ranks by $S(c)$, the sum of raw $r_q(c)$ values, and confidence as a tie-breaker. A method’s rank is determined by its best permitted configuration for the Case.

For an unknown attribute $a$, the algorithm enumerates permitted classes $v\in V_a$ and recalculates the ranking $R_{a\leftarrow v}$. A question has high priority if different values change the leading candidate or the set of excluded candidates; it has medium priority if only the top three change. If the order remains stable over the evaluated domain, the question is not asked at this point. Incomplete enumeration does not establish stability.

Each follow-up question explains how the answer could affect the decision. The initial experiment tests a hypothesis that could change the choice among promising candidates with insufficient evidence: it compares candidates on representative samples against an independent reference and agreed acceptance criteria.

## What the Expert Receives

The ranked list includes the method, sample interface, configuration concept, four technical scores, suitability from 0 to 36, a separate confidence assessment, and traceable factor contributions. It also provides reasons for exclusions, assumptions, decision-sensitive follow-up questions, and an initial experiment. The expert can correct a fact or condition and obtain a recalculated result with an updated trace.

Detailed specification: [rule registry and engine contract (Russian)](spectroscopy-rules/00-README.md). Its thresholds and weights are initial project parameters. The clarifications of official Noul/Score semantics and the API in this README should be considered when implementing the JEV adapter.

Official TypeSafe pages were checked on 18 October 2026. The sources used are typesafe.ai and docs.typesafe.ai; similarly named sites and third-party summaries were not used as the basis for the formulas.

## Quick start

```bash
pip install -r requirements.txt
LLM_MOCK=1 python run_case.py          # full pipeline with built-in examples, no API key, no cost
```

Live mode with real model calls: copy `.env.example` to `.env`, replace `[API KEY needed]` with your key and set `LLM_MOCK=0`:

```
ANTHROPIC_API_KEY=[API KEY needed]      # steps A and B (Claude)
OPENROUTER_API_KEY=[API KEY needed]     # optional Jev cross-check (JEV_LIVE=1)
LLM_MOCK=0
```

`.env` is git-ignored; keys never go into the repository.
Web app: `cd backend && pip install -r requirements.txt && uvicorn app.main:app`, then `cd frontend && npm install && npm run dev`.

API costs per analysis (about $0.06): [docs/api-costs.md](docs/api-costs.md).
Deutsch: [README.de.md](README.de.md).
