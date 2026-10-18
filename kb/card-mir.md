---
id: card-mir
method: mir
status: draft-unverified
source: general knowledge, verify against AFS method comparison table (Fri 16.10)
---

# Mid-infrared absorption, usually ATR (approx. 2.5–16 µm, 4000–600 cm-1)

## What it sees
Fundamental vibrations, sharp molecule-specific bands: functional groups, reaction intermediates, specific components in mixtures.

## Strengths
- High chemical specificity, good for multi-component quantification
- ATR works directly in strongly absorbing liquids, short effective path
- Calibrations relatively generic and transferable
- Strong for reaction monitoring in organic solvents

## Limits and typical exclusions
- Water absorbs strongly, aqueous media limit usable regions and sensitivity
- MIR fiber links (polycrystalline/silver halide, chalcogenide, hollow waveguide) are much shorter and costlier than silica links; the AFS materials show 2 m example IR cables (S02 p.9) and give no maximum length, so the link length and routing must be confirmed by AFS (gates rule L-LINK-LENGTH-MIR)
- ATR crystal can foul or be attacked, fouling reduces signal
- Fibers and crystals limit maximum temperature and chemical compatibility

## Probes and fibers
ATR immersion probes with diamond, ZrO2 or Si crystals on polycrystalline IR fibers, ATR loops, flow cells.

## Typical in-line uses
- Reaction monitoring and kinetics in organic synthesis
- Concentration of several components in liquids, e.g. alcohol, sugars, acids
- Bioprocess substrates and products with ATR (with water handling)

## How it maps to engine features (draft for Yarik)
phase=liquid → bonus; water_level=high → penalty; distance_class=far → hard limit; fouling_risk=high → penalty; temperature_class=very high → check probe

## AFS source
- document: TBD
- page: TBD
