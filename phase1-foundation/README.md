# Phase 1 — Foundation

Sets up the complete project skeleton, database, auth, and webhook infrastructure.

## What's included

| Area | Files |
|---|---|
| Monorepo config | `package.json`, `turbo.json`, `docker-compose.yml` |
| Database schema | `supabase/migrations/001_initial_schema.sql` |
| FastAPI app | `apps/api/main.py`, `config.py`, `database.py` |
| Auth middleware | `apps/api/middleware/auth.py` |
| Billing adapters (base + LS + Paddle) | `apps/api/adapters/billing/` |
| Webhook receiver | `apps/api/routers/webhooks.py` |
| Celery worker | `apps/api/workers/` |
| Next.js 15 shell | `apps/web/` |
| Shared types | `packages/shared-types/` |

## Setup order

1. Run `supabase/migrations/001_initial_schema.sql` in Supabase SQL editor
2. Copy `.env.example` → `.env` and fill in keys
3. `docker-compose up -d redis`
4. `cd apps/api && pip install -r requirements.txt && uvicorn main:app --reload`
5. In a new terminal: `celery -A workers.celery_app worker --loglevel=info`
6. `cd apps/web && npm install && npm run dev`
