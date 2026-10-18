---
id: card-raman
method: raman
status: draft-unverified
source: general knowledge, verify against AFS method comparison table (Fri 16.10)
---

# Raman scattering (laser, often 785 nm, also 532 or 1064 nm)

## What it sees
Vibrational fingerprint like MIR but via scattering: C=C, S-S, aromatics, polymorphs, inorganic and symmetric bonds.

## Strengths
- Water is a weak Raman scatterer, very good for aqueous and bioprocess media
- Silica fibers, analyzer can be far from the process
- Measures through glass windows and sight glasses
- Specific, multi-component, polymorph and crystallinity information

## Limits and typical exclusions
- Fluorescence of the sample or matrix can swamp the Raman signal, longer wavelength lasers reduce this
- Intrinsically weak signal, limited sensitivity for trace components
- Laser can heat or damage dark or sensitive samples
- Laser safety, and in hazardous areas explosion protection (ATEX) must be considered
- Strong absorbing or highly colored samples are difficult

## Probes and fibers
Immersion probes with sapphire window, non-contact optics through windows, ball-lens probes, sterilizable bioprocess probes.

## Typical in-line uses
- Glucose, lactate, ammonium-related and other components in cell culture and fermentation
- Polymerization and crystallization, polymorph monitoring
- Aqueous chemistry where MIR suffers from water

## How it maps to engine features (draft for Yarik)
water_level=high → bonus; fluorescence_risk=high → hard penalty or blocker; hazardous_area=yes → flag ATEX; concentration_level=trace → penalty; distance_class=far ok

## AFS source
- document: TBD
- page: TBD
