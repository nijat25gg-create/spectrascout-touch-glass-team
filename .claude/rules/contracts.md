---
paths:
  - "contracts/**"
  - "backend/app/schemas/**"
---
Contracts are shared by 5 people. Additive changes only (new optional fields).
After editing: run check_contracts.py, regenerate schemas with export_schemas.py,
update the matching example, and list who is affected (backend, frontend, engine).
Never duplicate contract models in backend/: import them from contracts.models.
