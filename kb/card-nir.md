---
id: card-nir
method: nir
status: draft-unverified
source: general knowledge, verify against AFS method comparison table (Fri 16.10)
---

# Near-infrared absorption / diffuse reflection (approx. 780–2500 nm)

## What it sees
Overtones and combination bands of C-H, O-H, N-H: water/moisture, alcohols, sugars, fats, proteins, hydroxyl number.

## Strengths
- Long silica fibers possible, analyzer can sit far away from the process
- Diffuse reflection on solids and powders without sample prep
- Deep penetration, water is not opaque so aqueous systems are possible
- Robust, established in pharma and food PAT

## Limits and typical exclusions
- Weak, broad, overlapping bands, needs chemometric calibration with reference data
- Calibrations transfer less easily between instruments than MIR
- Limited sensitivity for trace components, typically major and minor components
- Strong water bands can mask small analyte signals in very dilute aqueous samples

## Probes and fibers
Diffuse reflection probes for powders and granules, transmission/transflection probes for liquids, long silica fiber cables.

## Typical in-line uses
- Residual moisture in drying of powders
- Blend uniformity, API content in solids
- Fat, protein, moisture in food
- Hydroxyl number, octane, composition in petrochemicals

## How it maps to engine features (draft for Yarik)
phase=solid powder → strong bonus; water_level any; concentration_level=trace → penalty; distance_class=far → bonus

## AFS source
- document: TBD
- page: TBD
