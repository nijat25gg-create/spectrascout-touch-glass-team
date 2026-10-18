---
name: afs-premise-check
description: Check an AFS answer before it goes out - what must never be invented, common mistakes, citation and unit rules. Use when writing or reviewing step B reasoning, kb cards or rules.
---

# AFS premise check

## Never invent
- measured spectra or experimental results;
- accuracy, detection limits, response times, fiber lengths or other performance figures that no source supports;
- the client's sample composition, concentrations or answers to the assistant's questions;
- AFS product codes, prices or component ratings that are not in the sources;
- guarantees: a published application is a reason to test a method, not proof that it will work for a new customer.

## Common mistakes
- a central recommendation that rests on an invented figure, or on a source that does not say what is claimed;
- a citation that is unrelated or stretched beyond its scope (a laboratory study cited as proof of process or clinical readiness);
- missing client facts filled in as if they had been given;
- length or confidence taken as quality: a short, well-founded answer beats a long, assertive one.

## Citations
- Every important claim has a source and a page. Pages are 1-based PDF pages.
- The page must support the claim at the same scope (lab or process, sample type, prototype or product). A source ID next to a sentence is not proof.
- If the support is missing, drop the claim or mark it as an assumption.

## Units and ranges
- Always state units. A nominal method range is not the range of a specific instrument, fiber or probe.
- Raman: state the excitation wavelength separately from the Raman shift.

## Premise traps
| Trap | Method A (`rules/gates.yaml`) | Method B (`rules/b/rules_b.yaml`) |
|---|---|---|
| Calibration or model is not transferable as is | `P-CALIBRATION` | `R_Q1_06` |
| Fluorescence needs a defined fluorescent species or a justified indicator | `P-NO-FLUOROPHORE` | `R_Q1_F01`, `R_Q1_F02` |
| The existing fiber must carry the method's spectral range | `P-FIBER-RANGE` | `R_Q3C_08`, `R_Q3P_03` |
| Research or clinical evidence is not process readiness | `P-EVIDENCE-SCOPE`, `P-CLINICAL-SCOPE` | `R_Q4_07` |
| No measurable target yet | `P-TARGET-UNDEFINED` | `needs_target`, `R_Q1_01` |

The page for each trap is in the `source` field of the rule.
