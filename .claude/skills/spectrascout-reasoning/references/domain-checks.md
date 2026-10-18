# Domain checks

Apply relevant checks to the caller-selected assessment; engine-specific eligibility language applies only to method A. For method B, preserve Case boundaries, facts_b statuses and the supplied rubric. These checks generate explanations, questions and expert review items; they do not assign scores or eligibility. Source-supported points use evidence.md. Other engineering checks are proposed review questions, not established specifications.

## Analytical chemistry and spectroscopy

For the chemical basis of an explanation, consult [chemistry-foundations.md](chemistry-foundations.md): bonding/selection rules, organic groups, environment effects and mixture interpretation. Keep that explanatory reference separate from deterministic gates.

- Define the measurand independently of the instrument already owned. Distinguish concentration, composition, contamination identity, class and a trend. Ask whether the reference assay measures the same quantity and sample at the same time.
- For NIR, explain overlapping overtone/combination bands, matrix-specific calibration and sensitivity to physical variation (S01 p.10,17–18). Do not infer calibration validity from the same instrument or nominal analyte name.
- For Raman, keep laser excitation wavelength in nm distinct from shift in cm^-1. Check fluorescence background, signal level and process compatibility (S01 p.11–12). A reported 785 nm setup in S01 p.15 is an example, not an optimal customer prescription.
- For MIR ATR, check contact and the local interface as well as chemical information. Surface fouling or an unrepresentative contacted phase can decouple the spectrum from bulk composition (S01 p.10; REF D06–D07).
- For fluorescence, ask which fluorophore, marker or independently validated proxy produces target-related emission. Include excitation/emission, background, quenching/inner-filter effects as experimental questions where relevant. Do not label glucose or viable biomass a direct measurement on sensitivity grounds alone (S01 p.5,12,16; S04 p.4).
- For UV/Vis, specify whether absorption or turbidity/scattering is being interpreted. Optical density does not independently establish viability (S01 p.16; REF method overview).
- For combinations, state the hypothesis of complementary information. Synchronize time and sampling location; acknowledge different penetration depths. Test each method separately before fusion (S01 p.7–9; S04 p.3–4).

## Optics, specialty fibers and optoelectronics

The useful band requires overlap across every relevant component. An overlap is necessary, not proof of sufficient throughput or signal-to-noise. FTIR describes acquisition, not an independent sample interaction mechanism.

- Check delivered and returned wavelengths, material windows, attenuation over actual length, bends/routing, connector/coupling losses, detector response and source output. Unknown length remains unknown.
- A Vis/NIR silica cable is not justified as the transport path for the MIR bands described in S02 p.6. Flag incompatibility of that proposed path without declaring MIR ATR itself impossible or changing the engine's method state. Ask about a compatible MIR link or analyzer placement.
- PIR, chalcogenide, fluoride and hollow waveguide ranges are alternative engineering leads requiring configuration review, not interchangeable drop-in replacements or permission for arbitrary distance.
- Check temperature, pressure, chemical compatibility, crystal/window, sealing and cleaning requirements against actual component documentation. Metal coating, PEEK or diamond mentions do not certify the whole assembly.
- Use laser physics and optoelectronics to ask about excitation/background/filtering and sample heating when relevant. Do not add therapeutic laser advice to a spectroscopy enquiry.

## Materials science and characterization

Use solid-state, polymer, thin-film, semiconductor and nanomaterial knowledge only when those materials affect the sample, interface or optical chain. Relevant questions include heterogeneity, particle size, phase/state, film thickness, scattering, temperature-driven changes and surface deposits. Do not infer a molecular identity from an application label or invent mechanisms without analytical evidence.

Chromatography, MS, microscopy and imaging may characterize an unknown or supply an independent label/reference. Their appropriateness depends on the actual analyte/matrix. An existing laboratory assay is preferable to an invented reference technique when it measures the requested quantity adequately.

## Instrumentation, metrology and automation

Account for reference uncertainty, sample handling, time alignment, drift, response delay, repeatability and between-run reproducibility. Distinguish precision from bias and predictive accuracy. Do not report LOD/LOQ without a justified definition and supporting measurements.

LabVIEW experience translates into practical acquisition requirements: synchronized timestamps, instrument/configuration identifiers, calibration version, reference-sample IDs and quality flags. Do not require LabVIEW or a new software integration unless requested.

## R&D and commercialization

Sequence evidence: measurement feasibility → representative pilot → application validation → deployment decision. Use process modeling to identify nuisance variables and dynamics to test, not to fabricate observations. Compare operational complexity, maintainability and reference burden after feasibility is established. Qualitative cost ratings do not provide prices or ROI.

For biomedical requests, identify whether evidence concerns model tissue, in vitro human material or in vivo use. Explain the demonstrated scope, then propose the next research validation with the responsible clinical team. Never convert exploratory discrimination into an approved surgical decision system. Conference/event organization is not a technical decision criterion for this service.
