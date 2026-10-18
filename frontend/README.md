# Frontend

Owner: frontend.

The expert-facing briefing: use-case input, parameters with status, questions, recommended and rejected methods, rationale, first experiment, risks. Parameter editing triggers recalculation. PDF export of the briefing.

## Run locally

Start the backend on port 8000, then from `frontend/`:

```bash
npm install
npm run dev
```

Open http://localhost:5173. The page calls `POST /api/assessments`. Vite forwards that to FastAPI `POST /assessments`. The same `/api` paths are used after deployment: `deploy/nginx.conf` serves this frontend and forwards `/api/` to FastAPI.

```bash
npm run build
```
