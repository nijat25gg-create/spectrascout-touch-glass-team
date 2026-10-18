# legacy (do not use)

The first rules engine (points per feature, `rules_v02.yaml`) was retired on 18.10: the team switched to
the gates engine (`rules/gates.yaml`, `engine/gates.py`). `engine.score_methods` now fills C5 from the gates.

Kept here only for reference and for comparing old and new rankings (`python legacy/selftest_v02.py`).
Nothing in the product imports it. Delete this folder in one commit after the demo.

| File | Was |
|---|---|
| `rules_v02.yaml` | `rules/rules.yaml` |
| `rules_template_v02.yaml` | `rules/_template.yaml` |
| `score_v02.py` | `engine/score.py` (reads `rules_v02.yaml` next to it) |
| `selftest_v02.py` | `engine/selftest.py` |

Why retired: points instead of evidence; a water penalty that rejected NIR/MIR for percent-level analytes
(yogurt fat/protein, ethanol in beer); `R-MIR-FIBER-LENGTH: block` rested on a fiber length the AFS
materials do not give. See `docs/rules-v2.md`.
