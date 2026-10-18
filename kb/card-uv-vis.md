---
id: card-uv-vis
method: uv_vis
status: draft-unverified
source: general knowledge, verify against AFS method comparison table (Fri 16.10)
---

# UV-Vis absorption (approx. 200–800 nm)

## What it sees
Electronic transitions: conjugated systems, aromatics, colored species, many metal ions and complexes, nitrate and other UV-active ions.

## Strengths
- Simple, robust, cheap hardware, quartz fibers work well and can be long
- Very sensitive for strong absorbers, low concentrations possible
- Fast, good for kinetics and endpoint detection

## Limits and typical exclusions
- Low chemical specificity, broad overlapping bands, mixtures need chemometrics
- Analyte must absorb in UV-Vis, many aliphatics and sugars do not
- Turbidity, bubbles and particles scatter light and distort absorbance
- High concentrations saturate, short path length or ATR-UV needed
- Deep UV transmission of fibers can degrade (solarization), use solarization-resistant fibers

## Probes and fibers
Transmission/immersion probes with fixed path length, ATR-UV probes for highly absorbing media, reflection probes for solids.

## Typical in-line uses
- Reaction endpoint of colored or aromatic species
- Dye, API or metal ion concentration in clear liquids
- Nitrate/organics in water

## How it maps to engine features (draft for Yarik)
phase=liquid or gas best; turbidity=high → penalty; analyte_type=chromophore → bonus; concentration_level=trace ok if strong absorber

## AFS source
- document: TBD
- page: TBD
