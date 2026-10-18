---
id: card-fluorescence
method: fluorescence
status: draft-unverified
source: general knowledge, verify against AFS method comparison table (Fri 16.10)
---

# Fluorescence (excitation UV/Vis, also 2D excitation-emission)

## What it sees
Fluorophores: aromatic amino acids, NADH, flavins, some APIs, oils, dyes, tagged compounds.

## Strengths
- Extremely sensitive, trace levels possible
- Simple fiber probes, silica fibers
- 2D fluorescence gives fingerprints of biological state

## Limits and typical exclusions
- Only fluorescent analytes, or indirect correlation
- Quenching, inner-filter effects at higher concentrations, matrix effects
- Turbidity and scattering distort signals
- Signal often not linear over wide concentration ranges

## Probes and fibers
Bifurcated reflection/immersion probes, multi-wavelength excitation, sterilizable bioprocess probes.

## Typical in-line uses
- Biomass and metabolic state in bioprocesses (NADH, tryptophan)
- Trace oil in water
- Low-level fluorescent APIs or contaminants

## How it maps to engine features (draft for Yarik)
analyte_type=fluorophore → bonus; concentration_level=trace → bonus; turbidity=high → penalty

## AFS source
- document: TBD
- page: TBD
