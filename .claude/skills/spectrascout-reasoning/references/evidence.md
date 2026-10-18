# Evidence map

Authoring/review reference, not included by the context assembler. In runtime briefings, use only references permitted by explain_system.md and supplied kb_card/source data. CH01–CH05 are background only and must not be cited in the briefing.

Compiled on 2026-10-18 from supplied local materials. This is a curated interpretation, not a replacement rules engine or a certified AFS specification. Domain status: draft-unverified pending Nikita. Original files remain in D:/Downloads/materials; this package contains paraphrases and locators, not redistributed publications.

## Source register

| ID | File | Inspected support and limits |
|---|---|---|
| REF | AFS_Examples_and_Reference.docx | Sections 1–5; development enquiries, worked examples, evidence limits, source register and method overview. Constructed scenarios without measurements. The challenge brief referenced here was not supplied. |
| TABLE | AFS_method_comparison_table.xlsx | method_comparison rows 2–20 and notes rows 1–7. Transcription of S01 p.6 for AFS review. Qualitative sensitivity/selectivity/cost are not numerical performance or product specifications. |
| S01 | S01_Multispectral_Laboratory.pdf | Main technical overview. p.5 method physics; p.7–9 fusion and alignment; p.9–12 instrument concepts; p.14–15 powder/API; p.16 bioprocess; p.17–18 dairy. Application statements justify testing, not customer-specific guarantees. |
| S02 | S02_AFS_Process_Control_Slides.pdf | p.6 fiber families, p.13 water in petroleum, p.14 hot polymer/API visually checked as rendered slides. Other slides text-extracted; do not claim figures on those slides were visually verified. |
| S03 | S03_LED_Kidney_Study_2017.pdf | p.1 abstract: two LED sensor prototypes, 14 in vitro samples from 7 patients. DOI 10.3390/s17081914. Does not establish readiness for live surgical decisions. |
| S04 | S04_Combi_MIR_Fluorescence_2021.pdf | p.1 simultaneous ATR-MIR/fluorescence concept; p.3 chicken breast/fat/liver model samples; p.4 exploratory class separation and application constraints. DOI 10.1021/acs.analchem.1c00080. Not independent clinical validation. |
| S05 | S05_AFS_Flyer.pdf | Company/service positioning. Not evidence of accuracy, delivery specifications or suitability for a customer. |
| S06 | S06_Laboratory_Link.txt | Contains a laboratory URL only. Website was not fetched; do not cite its contents as inspected. |

## Claim-to-source routes

| Claim or question | Locator | Permitted interpretation |
|---|---|---|
| NIR nominal 780–2500 nm; broad overlapping bands | S01 p.10 | Method overview; actual instrument/fiber range still needs checking. |
| Powder API feasibility with NIR reflection and Raman | S01 p.14–15; REF worked D01 | Explain these candidates if the engine supplies them. New formulation requires matrix-specific validation. |
| Raman signal and fluorescence background | S01 p.11–12 | Check signal/background experimentally; do not assign a universal detection limit. |
| Fluorescence requires an emitting species or justified indicator | S01 p.5,12,16; S04 p.4 | Sensitivity alone does not justify glucose or viable-cell quantification. |
| Dairy geometry depends on optical behavior | S01 p.17–18; REF worked D02 | Reflection for opaque concentrate, transmission/transflection to investigate clear streams, tested over changing turbidity. No universal winner for all streams. |
| UV/Vis biomass-related signal versus metabolites | S01 p.16 | Separate turbidity/cell-density proxy from viability and biochemical concentration. |
| Fiber transmission windows | S02 p.6, visually inspected | Approximate family windows only; no cable-length, loss or power-budget approval. |
| Petroleum water and MIR ATR | S02 p.13, visually inspected | Published application lead. Graph concentrations are example samples, not the customer's range or a detection limit. |
| API in hot polymer extrusion | S02 p.14, visually inspected | Feasibility precedent for NIR reflection/MIR ATR; does not rate the customer's probe at temperature or pressure. |
| Combining measurements | S01 p.7–9; S04 p.1,3–4 | Need aligned location/time and a comparison with single-method baselines. Same contact point need not mean identical sampled depth/volume. |
| Research LED kidney sensor | S03 p.1 | In vitro proof of concept on a small patient set; no inference of in vivo readiness. |

## Numerical and citation caveats

S02 p.6 shows approximately: UV/Vis silica 0.19–1.2 µm, Vis/NIR silica 0.35–2.4 µm, As-S chalcogenide 1.1–6.5 µm, PIR 3–17 µm, hollow waveguides 2–18 µm, indium fluoride 0.3–5.5 µm and zirconium fluoride 0.3–4.5 µm. These are family-level plotted windows. S02 p.8 describes PIR as 3–16 µm; preserve the source/configuration distinction instead of claiming an exact guaranteed cutoff. A long silica link example on p.7 must not be transferred to MIR fibers.

TABLE optical_path_or_depth mixes different physical quantities across geometries. In particular, the ATR 1–6 µm entry is not a bulk transmission gap, universal penetration depth or probe dimension. Treat the entries as orientation only.

S01 p.16 gives illustrative concentration/sensitivity claims. Do not reuse them as customer-specific LOD/LOQ or a rule threshold. S01 p.14 references a separate 2017 kidney study, Sensors 17(11), 2548; it is not the supplied S03 LED paper, Sensors 17, 1914. Match title and DOI rather than joining evidence by year/topic.

If source passages conflict or contain a questionable detail, preserve the relevant locator, explain the conflict and request expert review. Do not silently convert source text into a verified chemistry rule. In particular, avoid reproducing peak assignments from S04 p.3 without expert checking when an exact assignment matters.

External literature, when explicitly supplied to the service, is supplementary. Retain its identifier, locator, short supporting passage, and sample/validation scope. Failed or timed-out retrieval means unavailable evidence, not a negative finding. Version 1.1.0 adds general chemistry sources CH01–CH05 in [chemistry-foundations.md](chemistry-foundations.md); these were checked separately and do not extend the AFS evidence to new product-performance claims.
