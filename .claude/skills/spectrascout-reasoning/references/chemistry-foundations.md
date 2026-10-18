# Chemistry foundations for spectroscopy reasoning

Domain status: draft-unverified pending Nikita. CH01–CH05 are background only: never cite them in the briefing or emit them as kb_card/source entries. This reference supports explanation and experimental design after engine scoring. It supplies no eligibility decisions, scores, instrument specifications or universal calibration limits. The original chemist-analyst skill supplies the structure/property and analytical-validation approach; the sources below support the focused spectroscopy content.

## Read by question

| Reasoning need | Read |
|---|---|
| Why a bond may produce different IR/Raman information | Bonding and selection rules |
| What organic groups may contribute to a known sample | Functional groups |
| Why the same composition may give different spectra | Environment and chemical state |
| Why a mixture prediction might be misleading | Mixtures and quantitative interpretation |
| How to apply the chemistry without changing the ranking | Application and explanation pattern |

## Bonding and selection rules

Bond vibrations involve atomic motion and the molecular electronic response. IR activity requires a change of dipole moment during a vibration; Raman activity requires a change of polarizability. A mode can be active in both. Thus, neither a polar/nonpolar label nor the presence of a bond alone predicts a useful measured peak. [CH01, theoretical background]

MIR primarily supplies fundamental vibrational information; NIR contains overtones and combination bands, often involving O-H, N-H and C-H groups. These broad overlapping contributions explain why a plausible chemical relationship still needs matrix-specific calibration. Do not label NIR a direct measurement of hydrogen bonds or equate an NIR feature with a unique molecule. [S01 p.5,9–11]

Practical inference: complementary IR/Raman information can motivate a comparison of engine-supplied candidates. It does not prove that fusion improves prediction. Account for background and acquisition geometry before interpreting a weak or missing band. [S01 p.7–9,11]

## Functional groups

Use the customer's stated compound/structure or an independent identification. These are signal hypotheses, not a method for filling unknown extraction attributes. Approximate MIR regions below are orientation values for common organic compounds, not spectral windows to configure automatically. A band may overlap or lie outside usable hardware coverage.

| Known group | Approximate MIR cue, cm^-1 | Interpretation limit |
|---|---|---|
| Aliphatic C-H | 2850–2960 stretching | Common to many organic constituents; not a selective API marker. |
| Alcohol O-H | Broad stretching; environment dependent | Water and other hydroxyl-bearing constituents may overlap. |
| Amine N-H | 3300–3500 stretching | Do not treat amines and amides as identical chemical environments. |
| Carbonyl C=O | Often 1670–1780 stretching | Ester, ketone, aldehyde, acid and amide environments differ. |
| Aromatic ring | Common ring contributions around 1450–1600 | A ring-related feature alone does not identify a molecule. |

The orientation regions and group distinctions come from CH02 Table 12.1 and CH03 sections on the respective groups. Conjugation can shift carbonyl absorption; hydrogen bonding broadens alcohol O-H features. Do not force a peak into a fixed lookup value. [CH03]

For acids, esters and amides, verify which group is actually present rather than treating all carbonyl-containing species as equivalent. Likewise, a carbohydrate, protein, lipid or polymer is a family containing multiple chemical environments; its name does not establish a unique analyte peak. Request structure/composition and a suitable reference when that distinction affects interpretation.

Keep functional-group evidence separate from identity, identity separate from concentration, and concentration separate from a quality decision. Do not conclude absence from an undetected feature without assessing overlap, background, coverage and signal quality.

## Environment and chemical state

Hydrogen bonding and temperature can change spectral shape independently of target concentration. JASCO's pure-water experiment demonstrates temperature-dependent NIR absorption associated with changing hydrogen-bond populations; that experiment supplies no correction coefficient for a customer's matrix. [CH04, results/conclusions]

When relevant, ask whether solvent, pH/protonation, ionic environment, hydration, phase, crystallinity or formulation changes. Treat these as variables to investigate, not explanations established by the enquiry alone. Raman can carry phase/polymorph and crystallinity information as well as composition information. [CH05, spectrum overview and applications]

Translate a suspected environment effect into a test: hold composition constant while varying the relevant condition, then change composition under controlled conditions. Log actual sample temperature and sample preparation. A hot-polymer spectral change, for example, should not automatically be called API loss; ask for paired chemical reference results and investigate physical-state effects.

## Mixtures and quantitative interpretation

Several constituents can contribute to the same region. Mixture spectra can support quantitative models when independent references and representative variation establish the relationship; an isolated library match or band assignment does not demonstrate selectivity in the process. Raman mixture analysis may require chemometrics. [CH05, qualitative/quantitative and mixtures sections; S01 p.5,10–12]

In transmission, use Beer-Lambert reasoning only with a defined path and suitable optical behavior. Do not apply a constant transmission path model directly to scattering reflection or an ATR interface. Revisit geometry as turbidity changes. [S01 p.17–18; TABLE notes]

A model may predict a target through correlated constituents rather than a uniquely target-specific signal. Challenge that relationship by varying relevant matrix constituents independently where possible. A new API/excipient blend can change both the chemical contributions and physical sampling; adding a second spectrum does not certify transfer of the old calibration. [REF worked D01; experiment-design.md]

For an unknown contaminant, an observed difference is a characterization lead. Establish identity or the affected quality variable with an appropriate independent method before claiming a selective quantitative response.

## Application and explanation pattern

Use these routes only to focus questions and experiments:

- **Water in petroleum:** distinguish the requested water measurand and sample representativeness; investigate whether phase distribution or interface contact changes the response. Use the published ATR application as a test lead, not a customer calibration. [S02 p.13]
- **Dairy:** investigate composition together with temperature, texture and scattering; a broad organic signal is not independently a fat or protein result. [S01 p.17–18]
- **Bioprocess:** distinguish metabolite concentration, cell-density proxy, viable biomass and fluorophore-related response. A chemically plausible optical signal does not establish all four. [S01 p.5,12,16; REF method overview]
- **Tissue:** different biochemical contributions and sampled depths can explain complementary information; model-tissue discrimination remains distinct from a validated clinical classifier. [S04 p.1,3–4]

Write a compact rationale:

`Known chemistry → plausible signal → competing chemical/physical explanation → independent measurement that distinguishes them`.

If composition or spectra are missing, keep the chemistry conditional. Report a discrepancy with the engine as an expert review item; do not adjust eligibility or rank. If an exact peak assignment drives a technical decision, check a relevant compound/matrix source and obtain expert confirmation rather than extrapolating from this orientation table.

## Supplementary sources

Sources checked on 2026-10-18. These explain general chemistry and instrumentation; they do not establish AFS product performance. This reference is an original synthesis with paraphrased facts, not a reproduced textbook chapter. S01/S02/S04/REF/TABLE locators are defined in [evidence.md](evidence.md).

- **CH01:** Johannes Gutenberg University Mainz, [Raman scattering, advanced physical chemistry lab](https://interaktiv.chemie.uni-mainz.de/vpcf1/raman-man.en.html), theoretical background, dipole/polarizability discussion. Use only the cited selection-rule discussion; other equations on the page are not imported here.
- **CH02:** John McMurry, OpenStax, [Organic Chemistry 12.7, Interpreting Infrared Spectra](https://openstax.org/books/organic-chemistry/pages/12-7-interpreting-infrared-spectra), Table 12.1. General orientation values, not complex-mixture performance evidence.
- **CH03:** John McMurry, OpenStax, [Organic Chemistry 12.8, Infrared Spectra of Some Common Functional Groups](https://openstax.org/books/organic-chemistry/pages/12-8-infrared-spectra-of-some-common-functional-groups), alcohols, amines, carbonyls and hydrocarbons. Exact examples are context dependent; no complete lookup table is reproduced.
- **CH04:** JASCO, [Analysis of Hydrogen Bonding in Pure Water using Temperature-dependent Spectroscopy](https://www.jasco-global.com/solutions/analysis-of-hydrogen-bonding-in-pure-water-using-temperature-dependent-spectroscopy/), results/conclusions. A pure-water instrument experiment, not validation of an industrial matrix.
- **CH05:** HORIBA, [What is Raman Spectroscopy?](https://www.horiba.com/int/scientific/technologies/raman-imaging-and-spectroscopy/raman-spectroscopy/), spectrum overview, qualitative/quantitative analysis and mixture sections. General instrumentation guidance, not a guarantee of process selectivity or linearity.
