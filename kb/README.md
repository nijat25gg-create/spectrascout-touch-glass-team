# Knowledge base

Status of every file is in its header. `draft-unverified` = written before AFS materials arrived, Nikita checks it on Friday against the AFS method comparison table and adds the AFS document and page.

| File | What | Owner |
|---|---|---|
| `card-<method>.md` | One card per AFS method: what it sees, where it fails, probes, typical uses | draft Nidzhat, check Nikita |
| `expert-*.md` | Experience of the 5 interviewed chemists, no names | Nikita |
| `_card-template.md` | Empty card template | Nikita |
| `afs-qa.md` | Answers from the AFS Q&A session (Fri) | Nidzhat |
| `literature.md` | Published papers added to the case materials (DOI, licence, use); PDFs stay local in `materials/articles/` | team, check Nikita |

Rules for cards
- Only methods AFS offers: uv_vis, nir, mir, raman, fluorescence, scattering. MS, NMR, chromatography only as reference methods for calibration.
- Every claim gets a `source:` line. Until Friday many are `general knowledge, verify`.
- Step B of the LLM may only cite a card by its id, it never writes a page number itself.
