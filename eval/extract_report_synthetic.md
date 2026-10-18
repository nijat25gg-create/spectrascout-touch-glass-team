# Step-A extraction evaluation

Source of attributes: simulated full step A (final prompt 18.10), sonnet.
Simulated = a Claude subagent got exactly the step-A system prompt (`llm.extract.system_prompt()`) and the customer text, and its output went through the same normalisation (`llm.vocab.normalize_attributes`). It is NOT a live API call (no key was used). Live run: `python eval/extract_eval.py --live` with the key in .env.
Golden = hand-written expectations (eval/golden_cases.yaml). D = development, H = test (report only).

## SYNTHETIC S01–S04 (own texts, written without AFS materials; generalisation check)

Attributes: **29/29 match** (100%), 0 wrong, 0 missed, 16 extra (review: invention or gap in golden).
End to end (engine on our attributes vs golden expect): **4/4 cases without deviation**.

| Case | match | wrong | missed | extra | engine status · top | deviations |
|---|---|---|---|---|---|---|
| S01 | 7 | – | – | domain=other (assumed), sample_form=powder (known), matrix_aqueous=no (assumed), streams=1 (assumed) | provisional · K03, K04 | ok |
| S02 | 10 | – | – | targets_count=1 (known), quantitative=yes (known), streams=1 (assumed), justification=none_given (assumed), own_validation=no (known) | provisional · K05 | ok |
| S03 | 3 | – | – | quantitative=no (assumed), domain=other (assumed), streams=1 (assumed) | insufficient_information · – | ok |
| S04 | 9 | – | – | sample_form=soft_solid (assumed), optical_density=opaque (assumed), matrix_aqueous=yes (assumed), physical_variation=yes (known) | provisional · K03, K01 | ok |
