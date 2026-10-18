---
paths:
  - "frontend/**"
---
Plain JS, no frameworks. Vite only as dev server and build (npm run dev / build); the page calls relative /api paths, the Vite proxy and deploy/nginx.conf strip /api. Data shape = Briefing (C8) in contracts/models.py,
sample in contracts/examples/C8_briefing.example.json. UI texts in DE and EN via i18n.js.
Every number the expert sees must be traceable: show rule_id and note on click.
Handle loading, error (ErrorResponse E) and empty states.
