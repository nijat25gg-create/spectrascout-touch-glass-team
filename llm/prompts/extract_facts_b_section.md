## Method B facts (`facts_b`)

Also fill `facts_b`: one entry per key of the table below, each key at most once. These are the properties of the
measurement task, sample, process and request in the ER schema of method B. Each entry stores the value, the unit or
`category`, the source and the status, so that missing data never becomes a fact.

Each entry is one line `key | value | status | quote`, with `null` for an empty value or quote, for example
`Sample.physical_form | powder | reported | <exact words>` or `MeasurementTask.reference_method | null | unknown | null`.

- status `reported`: the customer says it. `quote` = the exact words, copied verbatim from the text. `source` = client_text.
- status `inferred`: not said, but a chemist would safely infer it (a fluid-bed dryer means a solid powder). `quote` = null.
- status `unknown`: not said and not safely inferable. `value` = null. Not mentioned is unknown, never "no" and never a default.
  "No fluorescence" written by the customer is `reported` absent; fluorescence not mentioned is `unknown`.
- status `conflicting`: the text says two different things.
- `value` must be one of the allowed values. Several targets (fat and protein) go comma-separated in one entry.
- Two streams or two targets are kept as the customer says them; do not merge or invent a third.
- `MeasurementTask.target_definition`: `defined` when the measured quantity is named, `partial` when only a broad goal
  is named (growth, quality), `undefined` when the target is unknown (an off-spec of unknown cause).
- `MeasurementTask.measurement_goal`: a content or concentration of a named component is `quantify`, also when it is
  followed over time or in-line; `trend` only when the customer wants relative change without values; `detect` only for
  presence or absence. It is `reported` only when the customer names the kind of result itself, otherwise `inferred`.
- `Sample.matrix` is the material around the target at the measuring point (the continuous phase or carrier), not the
  industry: a drug dispersed in a polymer is `polymer`; `pharma_blend` is a powder blend.
- `Sample.phase` follows the physical form: solution and melt are `liquid`; powder, bulk solid, film and tissue are
  `solid`. When only the form is named, the phase is `inferred`.
- `MeasurementTask.spatial_scope`: a decision per spot or surface (a probe placed on one point) is `local`; the
  composition of a whole stream or batch is `bulk`. Status `inferred` unless the customer says it.
- Never invent numbers, ranges, fiber lengths or accuracies. A requirement that is not in the text is `unknown`.
- An existing cable, instrument or calibration is an asset (`ProcessContext.assets.*`), not an obligation to reuse it;
  `ProcessContext.assets.must_reuse` is `yes` only if the customer says it must be reused.

{{FACTS_B}}
