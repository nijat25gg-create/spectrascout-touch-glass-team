# First feasibility experiment

This procedure carries forward the original chemist-analyst skill's useful analytical-method principles: define the target, connect structure to signal, test selectivity, compare independent references and document limitations. It replaces broad synthesis/mechanism tutorials with spectroscopy-specific experimental decisions. Proposed design practices below are guidance, not additional engine gates.

## Choose a falsifiable question

State the uncertainty the experiment will resolve. Examples: whether the requested analyte signal can be separated from matrix changes; whether a geometry retains usable signal over the observed turbidity range; whether a new formulation remains within the calibration's demonstrated domain.

If the target is undefined, first compare representative conforming/off-spec material with independent characterization. Identify the changed variable or analyte before promising a selective sensor configuration. Spectroscopy may screen differences without identifying their cause.

## Specify the minimal useful study

1. **Samples/states:** cover the client-agreed target range, relevant matrix variants and realistic process changes. Keep unknown ranges and sample counts pending agreement; do not invent them.
2. **Reference:** use an independent assay or label for each target, with uncertainty, sampling location, handling and timing. For viability, use a viability reference rather than a turbidity value relabeled as live biomass.
3. **Comparison:** test the engine-supported candidates and plausible geometries under comparable conditions. For fusion, retain single-method baselines on the same validation material.
4. **Controls:** deliberately vary relevant nuisance factors independently where practical: temperature, scattering, particle size, bubbles, contact, fouling, formulation, process stage or time delay. Include blanks/controls or mixtures only when meaningful for the analytical question.
5. **Acquisition:** keep spectra, timestamps, sample/reference IDs, settings, geometry, configuration and calibration version. For heterogeneous samples, align measurement location; for fast processes, align timing.
6. **Analysis:** establish signal quality and representativeness first. A calibration can follow if paired reference data support it. Fit preprocessing, feature selection and model parameters only within training partitions. Do not use validation results to select features and then report them as untouched validation.
7. **Validation:** hold out independent batches, process runs or samples as appropriate. Group repeated spectra from the same sample together. For biomedical work, separate patients across partitions; repeated points are not independent patients. A PCA plot is exploration, not a validated prediction metric.
8. **Decision:** compare with criteria agreed before testing. Report missing criteria as a decision dependency. A pilot without agreed targets can establish signal feasibility but cannot establish customer acceptance.

## Report meaningful outcomes

For concentration, consider held-out prediction error, bias, usable range, reference uncertainty, response delay and robustness. For classification, consider the error types relevant to the decision, class balance and independent validation unit. For a trend, ask whether the change is detected early and reliably enough for the intended decision. Evaluate drift/fouling and maintenance where process installation matters.

Recommend the simplest configuration that meets the agreed criteria on independent material. Additional modalities are justified only by a measured benefit relevant to those criteria.

For a formulation change, test the existing model on new representative material with new reference values. Updating or rebuilding the calibration may be necessary. Adding Raman does not make the old NIR calibration valid.

For a research sensor, first replicate technical measurements on the proposed setup, then validate on independent relevant material against an appropriate reference. Any prospective clinical study belongs to the responsible clinical/research team; this plan does not authorize live surgical decision use.
