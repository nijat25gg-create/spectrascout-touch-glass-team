# Response schema (shared contract)

> Superseded on 13 Oct by [`contracts/`](../contracts/README.md).

The single source of truth for every data format is `contracts/models.py` (Pydantic). JSON Schemas are generated into `contracts/schemas/`, one example per step is in `contracts/examples/`, and `python contracts/check_contracts.py` checks that everything fits together.

The final response the frontend renders is contract **C8 Briefing** (`contracts/examples/C8_briefing.example.json`).
