# Step-A extraction evaluation

Source of attributes: simulated step A (final prompt 18.10), sonnet subagents.
Simulated = a Claude subagent got exactly the step-A system prompt (`llm.extract.system_prompt()`) and the customer text, and its output went through the same normalisation (`llm.vocab.normalize_attributes`). It is NOT a live API call (no key was used). Live run: `python eval/extract_eval.py --live` with the key in .env.
Golden = hand-written expectations (eval/golden_cases.yaml). D = development, H = test (report only).

## DEV D01–D08

Attributes: **59/59 match** (100%), 0 wrong, 0 missed, 36 extra (review: invention or gap in golden).
End to end (engine on our attributes vs golden expect): **8/8 cases without deviation**.

| Case | match | wrong | missed | extra | engine status · top | deviations |
|---|---|---|---|---|---|---|
| D01 | 8 | – | – | targets_count=1 (known), matrix_aqueous=no (assumed), gmp=yes (assumed), asks=assessment (known) | provisional · K03, K05, K04 | ok |
| D02 | 9 | – | – | intended_use=pilot (assumed), matrix_aqueous=yes (assumed), streams=1 (known), asks=assessment (known) | provisional · K03, K01, K05 | ok |
| D03 | 8 | – | – | targets_count=1 (known), streams=1 (known), physical_variation=yes (known), asks=assessment (known) | provisional · K02, K03, K01 | ok |
| D04 | 8 | – | – | intended_use=pilot (known), streams=1 (assumed), physical_variation=yes (known), asks=assessment (known) | provisional · K05, K02, K01 | ok |
| D05 | 6 | – | – | matrix_aqueous=yes (assumed), streams=1 (assumed), physical_variation=yes (known), asks=assessment (known) | provisional · K08, K06 | ok |
| D06 | 7 | – | – | targets_count=1 (known), intended_use=pilot (known), matrix_aqueous=no (assumed), streams=1 (known), asks=assessment (known) | provisional · K03, K02 | ok |
| D07 | 7 | – | – | targets_count=1 (assumed), quantitative=yes (known), intended_use=pilot (known), matrix_aqueous=no (assumed), streams=1 (assumed), gmp=yes (assumed), asks=assessment (known) | provisional · K01, K03 | ok |
| D08 | 6 | – | – | targets_count=1 (assumed), quantitative=no (known), client_method=mir (known), asks=assessment (known) | provisional · K10, K01 | ok |

## TEST H01–H06 (report only, no tuning)

Attributes: **55/57 match** (96%), 1 wrong, 1 missed, 14 extra (review: invention or gap in golden).
End to end (engine on our attributes vs golden expect): **6/6 cases without deviation**.

| Case | match | wrong | missed | extra | engine status · top | deviations |
|---|---|---|---|---|---|---|
| H01 | 13 | – | – | matrix_aqueous=no (assumed), physical_variation=yes (known), gmp=yes (assumed), justification=none_given (assumed) | provisional · K03, K05, K04 | ok |
| H02 | 11 | – | – | targets_count=2plus (known) | provisional · K02, K03, K01 | ok |
| H03 | 11 | – | – | – | provisional · K05, K02, K03 | ok |
| H04 | 8 | – | – | targets_count=1 (known), quantitative=yes (known), matrix_aqueous=no (assumed), streams=1 (known), justification=none_given (assumed) | provisional · K03, K02 | ok |
| H05 | 4 | – | domain | quantitative=no (assumed), streams=1 (assumed) | insufficient_information · – | ok |
| H06 | 8 | target_defined: ours yes vs golden partial | – | targets_count=1 (assumed), quantitative=no (assumed) | outside_scope · – | ok |
