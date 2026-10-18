# Backend

Owner: backend.

API that orchestrates the pipeline and returns one assessment to the frontend. Data shapes follow the shared contracts in [contracts/](../contracts/README.md) (C1, C1b, C8, E). `POST /assessments` and `POST /assessments/recalculate` return briefing schema 0.2. The public `/api` prefix stays on the Vite proxy and `deploy/nginx.conf`; FastAPI does not expose it.

## Run locally

From `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

`GET /health` returns `{"status": "ok"}`.

The browser calls `POST /api/assessments` on the frontend origin. Vite in development and `deploy/nginx.conf` in production strip `/api` and forward the request to `POST /assessments`. FastAPI does not expose a second `/api` route. Direct calls to port 8000 stay on `/assessments`.

Settings are read from the environment and from the repository root `.env`. None are required. `LOG_LEVEL` defaults to `INFO`, `AI_TIMEOUT_SECONDS` defaults to `30`, and `AI_BASE_URL` stays empty until the AI component has an address. A shared HTTP client opens at startup and closes on shutdown. Each request is logged with its method, path, status, and duration.

```bash
pytest
```
