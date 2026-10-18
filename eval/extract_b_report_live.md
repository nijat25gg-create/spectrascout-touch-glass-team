# Step A (method B facts) vs eval/golden_b.yaml, live

| case | golden keys ok | wrong | missed | extra (review) | leader | expected | s |
|---|---|---|---|---|---|---|---|
| D01 | 8/8 | 0 | 0 | 2 | NIR | NIR, Raman | 26 |
| D02 | 7/7 | 0 | 0 | 9 | NIR, NIR | NIR | 31 |
| D03 | 6/6 | 0 | 0 | 5 | NIR | NIR | 26 |
| D04 | 7/7 | 0 | 0 | 6 | Raman, Raman | Raman | 30 |
| D05 | 6/6 | 0 | 0 | 3 | NIR, NIR | - | 25 |
| D06 | 6/6 | 0 | 0 | 5 | MIR | MIR | 26 |
| D07 | 7/8 | 1 | 0 | 4 | MIR | MIR, NIR | 28 |
| D08 | 8/8 | 0 | 0 | 3 | MIR | MIR, Fluorescence | 25 |

**Golden facts matched: 55/56. Leader as expected: 7/7.**

## D01
- headline: NIR and Raman lead (24/36); provisional until 'optical properties fluorescence' is checked.
- extra: CustomerRequest.asks=assessment (reported)
- extra: MeasurementTask.target_definition=defined (reported)

## D02
- headline: NIR leads (24/36); provisional until 'sample state constraints contact' is checked.
- status: Sample.variability.physical: got reported, golden inferred
- extra: CustomerRequest.asks=assessment (reported)
- extra: MeasurementTask.business_goal=pilot (reported)
- extra: MeasurementTask.spatial_scope=bulk (inferred)
- extra: MeasurementTask.target_definition=defined (reported)
- extra: MeasurementTask.time_requirements=given (reported)
- extra: ProcessContext.deployment_preference=in_line (inferred)
- extra: ProcessContext.temperature_range=unspecified (reported)
- extra: Sample.physical_form=emulsion (inferred)
- extra: Sample.sample_state_constraints.sampling=allowed (reported)

## D03
- headline: NIR leads (24/36); provisional until 'relevant components fluorophore' is checked.
- status: MeasurementTask.measurement_goal: got reported, golden inferred
- status: Sample.phase: got inferred, golden reported
- extra: CustomerRequest.asks=assessment (reported)
- extra: MeasurementTask.business_goal=lab_research (reported)
- extra: MeasurementTask.spatial_scope=bulk (inferred)
- extra: MeasurementTask.target_definition=defined (reported)
- extra: Sample.physical_form=solution (inferred)

## D04
- headline: Raman leads (24/36); provisional until 'optical properties fluorescence' is checked.
- extra: CustomerRequest.asks=assessment (reported)
- extra: MeasurementTask.spatial_scope=bulk (inferred)
- extra: MeasurementTask.target_definition=defined (reported)
- extra: MeasurementTask.time_requirements=given (reported)
- extra: Sample.physical_form=suspension (inferred)
- extra: Sample.variability.formulation=changed (reported)

## D05
- headline: NIR and UV_VIS lead (21/36); provisional until 'reference method' is checked.
- status: MeasurementTask.measurement_goal: got reported, golden inferred
- extra: CustomerRequest.asks=assessment (reported)
- extra: MeasurementTask.business_goal=lab_research (reported)
- extra: Sample.physical_form=suspension (inferred)

## D06
- headline: MIR and NIR lead (23/36); provisional until 'physical form' is checked.
- extra: CustomerRequest.asks=assessment (reported)
- extra: MeasurementTask.spatial_scope=bulk (inferred)
- extra: MeasurementTask.target_definition=defined (reported)
- extra: MeasurementTask.time_requirements=given (reported)
- extra: Sample.sample_state_constraints.sampling=allowed (reported)

## D07
- headline: MIR and NIR lead (25/36); provisional until 'sample state constraints contact' is checked.
- wrong: MeasurementTask.measurement_goal: got detect, golden quantify
- extra: CustomerRequest.asks=assessment (reported)
- extra: MeasurementTask.business_goal=lab_research (reported)
- extra: MeasurementTask.spatial_scope=local (inferred)
- extra: MeasurementTask.target_definition=partial (reported)

## D08
- headline: MIR leads (25/36); provisional until 'sample state constraints contact' is checked.
- status: MeasurementTask.target: got reported, golden inferred
- extra: CustomerRequest.asks=assessment (reported)
- extra: MeasurementTask.target_definition=defined (reported)
- extra: ProcessContext.deployment_preference=lab (reported)

