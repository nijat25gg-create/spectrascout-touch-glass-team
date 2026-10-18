## Attributes of the analysis request (v0.3)

Also fill `attributes`: one entry per attribute in the table below. The rules engine reads them and an expert checks them. These attributes follow their own rules below. The feature heuristics above (for example "fluorescence_risk: high for biological media") do NOT apply here.

{{VOCABULARY}}

### How to fill each entry
- `value` must be one of the allowed values of that attribute, spelled exactly as in the table. If nothing fits, set value null and status `unknown`.
- status `known`: the customer states it. Put in `quote` the shortest exact piece of the customer text that shows it (at least a few words), copied character for character. Do not translate, shorten inside, or paraphrase. A quote that is not in the text turns the value into `unknown`.
- status `assumed`: not stated, but every reasonable chemist would infer the same value from what is stated (a fermentation broth is water-based; a petroleum line carries a liquid). Set `quote` to null. If two readings are possible, use `unknown`. Never assume just to fill a gap.
- status `unknown`: not stated and not safely inferable. Set `value` and `quote` to null. An honest unknown becomes a question to the customer. A wrong guess hides that question.
- status `conflicting`: the text gives two incompatible values for the same attribute. Give the first value and set `quote` to null. Several streams or targets are NOT a conflict: set `streams` / `targets_count` to `2plus` and describe the FIRST stream or target named in all other attributes (`target_kind`, `optical_density`, ...). The assessment is made for that first one and flagged so the expert plans the others; do not leave those attributes unknown because there are two.
- Never invent numbers, ranges, temperatures, fiber lengths or accuracies.

### Silence is not a "no"
- A negation is a fact. "We have no reference method yet" → `reference_method = none` (known). "We have not yet selected a probe" says nothing about the fiber, so `existing_fiber` stays `unknown`.
- `none` is a value only when the customer says so: `client_method = none` ("we have no method in mind"), `existing_fiber = none` ("no fiber installed yet"), `cited_evidence = none`. If the customer says nothing about it, the status is `unknown`, never assumed `none`.
- A possibility the customer mentions counts as stated: "may be exposed to material build up" → `fouling = high` (known). "can become more turbid" or "becomes more optically dense during the run" → `optical_density = varies` (known).

### What the customer wants to know
- `target_kind`: what the measurement must report (the API, fat, protein, glucose, water, a contaminant, a tissue class). It is not the matrix. Water as a contaminant in oil gives `target_kind = water`. Composition changes of a product that contains a named active ingredient are about that ingredient → `api`. Two targets named → the first one (see conflicting).
- `target_class`: the concentration level of the target. Fill it only from a stated level or number (status known, quote the number): about 1 % or more → `major_component`; 0.1–1 % → `minor_component`; below about 0.1 % (ppm, traces) → `trace`. Otherwise `unknown`.
- `target_defined`:
  - `yes`: the substance or property is named, for example "API concentration" or "composition changes of a blend with a named API";
  - `partial`: several signals are mentioned but not defined as separate variables ("a biomass signal and a metabolic signal ... not defined as separate targets");
  - `no`: the customer cannot say which substance, property or quality variable should be detected.
- `targets_count`: `2plus` when two or more variables must be reported (fat and protein, glucose and lactate, two signals). `1` when one variable is named.
- `quantitative`: `yes` when a concentration, content or composition of a named component is to be followed ("API concentration", "water determination", "fat and protein analysis"); laboratory results of that component used as reference also mean `yes`. `no` only for classification (tissue types, good/bad) or for detecting an unnamed deviation. Otherwise `unknown`.
- `intended_use`:
  - `lab_research`: a laboratory or research study;
  - `pilot`: a pilot, trial or first comparison at the process;
  - `production`: routine production control;
  - `clinical_in_vivo`: only decisions about living patients.

### What is measured
- `domain` is the industry and product (pharma solid dosage, dairy, bioprocess, petroleum, polymer melt, tissue). `sample_form` is the physical state at the measurement point:
  - `powder` (also granules, pellets, flakes: any bulk particulate solid);
  - `liquid`;
  - `paste_melt` (melt, paste);
  - `soft_solid` (tissue, yogurt, butter);
  - `solid` (one solid piece or surface: tablet, sheet, film, a part);
  - `gas`.
- `optical_density`:
  - `clear`: you can see through it;
  - `turbid`: hazy or scattering, but light passes through;
  - `opaque`: no light passes, like milk concentrate, yogurt, cream, crude oil or a dense broth;
  - `varies`: the customer says it changes.
- `matrix_aqueous`: `yes` if the matrix is mainly water (cell culture medium, broth, whey). `no` for oil, polymer melt or dry powder.
- `streams`: `2plus` when two or more streams, lines or recipes with different optical behaviour must be covered. `1` when a single product, line or formulation is described.
- `physical_variation`: `yes` when temperature, texture, particle size, bubbles or recipe change between runs or during a run.
- `matrix_fluorescence` and `chromophore` are LAB CHECKS. Fill them only if the customer states them explicitly. Never infer them from the kind of sample.

### Where and how it is measured
- `temperature`: `ambient` up to about 40 °C, `elevated` 40–150 °C, `high` above 150 °C. "Hot" alone fits `elevated` or `high`; use `high` only for melts and similar processes that run above 150 °C.
- `fouling`: `high` if deposits, build-up, coating or sticky material at the probe are possible. `low` only if the customer says the window stays clean.
- `distance` = where the ANALYZER stands, not the measurement point:
  - `at_process`: at the line;
  - `outside_area`: outside the process area;
  - `other_building`: in another building.

  "A measurement closer to the process" describes the measurement point, not the analyzer.
- `link_confirmed`: always `unknown`. AFS confirms the link, the customer cannot.
- `existing_fiber`: only a fiber or cable the customer already has or plans. A silica fiber for the visible/NIR range → `silica_vis_nir`; for UV/visible → `silica_uv_vis`.
- `gmp`: `yes` (known) if GMP, cleanroom or sterile requirements are stated. Pharmaceutical production without such words → `yes` assumed.

### What the customer claims or asks (premises)
- A method, instrument or cable the customer already has or proposes is `client_method` / `existing_fiber`. It is never evidence that the method fits.
- `client_method`: the method the customer proposes or wants confirmed. If the customer names two methods to compare, give the first one named.
- `justification`:
  - `sensitivity_only`: the only reason given is that the method is sensitive;
  - `physical_basis`: the customer explains why the method sees the target;
  - `none_given`: a method is proposed with no reason at all.

  Fill it only if `client_method` is known.
- `asks`: what the customer wants from AFS. When several fit, take the most demanding one:
  - `readiness_proof`: proof that the method or sensor already works or is ready to use;
  - `approve_concept`: approve or confirm their own concept;
  - `exact_config_now`: a final configuration right away, before any test;
  - `assessment`: an assessment, comparison, concept or study.
- `cited_evidence`:
  - `research_paper`: a publication or paper;
  - `afs_application`: an AFS application note;
  - `business_material`: brochures, sales or marketing material.
- `reuse_calibration` (keep an existing calibration), `add_method_to_keep_calibration` (add a second method so the old calibration stays valid), `formulation_changed` (new API, excipients or recipe), `own_validation` (own data on the intended setup): `yes` / `no` only if stated.
