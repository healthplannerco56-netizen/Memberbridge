# MemberBridge
### Membership Billing Automation for Community Platforms

Automates community access, subscription syncing, failed payment handling,
and dunning workflows for creators using Circle, Skool, and Mighty Networks.

---

## Three-Phase Delivery

| Phase | What ships | When to build |
|---|---|---|
| **Phase 1 — Foundation** | Auth, DB schema, webhook infra, Paddle + LS adapters, base API | Start here |
| **Phase 2 — Core Product** | Circle adapter, automation engine, all dashboard pages | After Phase 1 is deployed |
| **Phase 3 — Growth** | Dunning emails, analytics charts, Celery Beat schedule | After first paying users |

---

## Phase 1 — Foundation

**Goal:** Working webhook pipeline from billing provider → database.

```
phase1-foundation/
├── supabase/migrations/001_initial_schema.sql   ← Run first in Supabase
├── apps/api/
│   ├── main.py              ← FastAPI app
│   ├── config.py            ← Settings (reads .env)
│   ├── database.py          ← Supabase client
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.toml
│   ├── middleware/auth.py   ← Clerk JWT verification
│   ├── adapters/billing/
│   │   ├── base.py          ← Abstract adapter + NormalizedBillingEvent
│   │   ├── lemon_squeezy.py ← Lemon Squeezy webhook adapter
│   │   └── paddle.py        ← Paddle Billing adapter
│   ├── adapters/community/
│   │   └── base.py          ← Abstract community adapter
│   ├── routers/
│   │   ├── webhooks.py      ← POST /webhooks/lemon-squeezy/{token}
│   │   ├── workspace.py     ← Workspace CRUD + default rule seeding
│   │   ├── integrations.py  ← Billing + community integration setup
│   │   ├── members.py       ← Member list + detail + manual sync
│   │   ├── automations.py   ← Rule CRUD + execution log
│   │   ├── events.py        ← Webhook event log + retry
│   │   └── dashboard.py     ← Stats + recent events
│   ├── services/
│   │   └── audit_service.py
│   └── workers/
│       ├── celery_app.py    ← Celery factory (Redis broker)
│       └── tasks.py         ← process_webhook_event task
└── apps/web/
    ├── app/
    │   ├── layout.tsx        ← Root layout (Clerk + fonts)
    │   ├── globals.css
    │   ├── auth/sign-in/    ← Clerk SignIn page
    │   ├── auth/sign-up/    ← Clerk SignUp page
    │   ├── dashboard/
    │   │   ├── layout.tsx   ← Protected layout (Sidebar + TopBar)
    │   │   └── page.tsx     ← Dashboard home (stats + event feed)
    │   └── onboarding/page.tsx  ← 3-step setup wizard
    ├── components/
    │   ├── shared/Sidebar.tsx
    │   ├── shared/TopBar.tsx
    │   ├── shared/StatusBadge.tsx
    │   ├── dashboard/StatsCards.tsx
    │   └── dashboard/EventFeed.tsx
    ├── lib/
    │   ├── api.ts            ← Full API client (all endpoints)
    │   └── utils.ts
    ├── types/index.ts
    ├── middleware.ts          ← Clerk route protection
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── postcss.config.js
```

### Setup

```bash
# 1. Run DB migration
#    Open Supabase → SQL Editor → paste 001_initial_schema.sql

# 2. Environment
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, CLERK_SECRET_KEY,
# RESEND_API_KEY, ENCRYPTION_KEY, REDIS_URL

# 3. Start Redis
docker-compose up -d redis

# 4. Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 5. Worker (new terminal)
celery -A workers.celery_app worker --loglevel=info

# 6. Frontend
cd apps/web
npm install
npm run dev
# → http://localhost:3000
# → API docs: http://localhost:8000/docs
```

---

## Phase 2 — Core Product

**Goal:** Members get auto-added/removed from Circle based on subscription events.

```
phase2-core/
├── apps/api/
│   ├── adapters/community/circle.py    ← Circle API adapter
│   ├── services/automation_engine.py  ← Rule evaluator + action dispatcher
│   └── routers/  (no new files — Phase 1 routers already cover Phase 2)
└── apps/web/
    ├── app/dashboard/
    │   ├── members/page.tsx
    │   ├── automations/page.tsx
    │   ├── events/page.tsx
    │   └── settings/
    │       ├── page.tsx
    │       └── SettingsClient.tsx
    └── components/
        ├── members/MembersTable.tsx
        ├── automations/AutomationsList.tsx
        └── dashboard/EventsTable.tsx
```

### Upgrade from Phase 1

```bash
# Copy Phase 2 files into your repo (same folder structure)
cp -r phase2-core/* your-repo/

# Restart API (no migration needed)
uvicorn main:app --reload --port 8000
```

---

## Phase 3 — Growth

**Goal:** Automated dunning emails + analytics charts + Celery Beat scheduler.

```
phase3-growth/
├── supabase/migrations/002_analytics.sql    ← Run in Supabase
├── apps/api/
│   ├── services/dunning_service.py    ← Schedules dunning emails
│   ├── services/email_service.py      ← Resend wrapper + templates
│   ├── services/analytics_service.py  ← Daily snapshot compute
│   ├── routers/dunning.py             ← Dunning CRUD + log
│   ├── routers/analytics.py           ← Trend + MRR endpoints
│   ├── workers/scheduled.py           ← Celery Beat tasks
│   └── main-additions.md              ← How to wire into main.py
└── apps/web/
    ├── app/dashboard/
    │   ├── dunning/
    │   │   ├── page.tsx
    │   │   └── DunningClient.tsx
    │   └── analytics/page.tsx
    ├── components/
    │   ├── analytics/MrrCard.tsx
    │   ├── analytics/MemberTrendChart.tsx
    │   └── analytics/MrrTrendChart.tsx
    └── lib/api-additions.ts            ← Methods to add to api.ts
```

### Upgrade from Phase 2

```bash
# 1. Run migration
#    Supabase → SQL Editor → paste 002_analytics.sql

# 2. Copy Phase 3 files
cp -r phase3-growth/* your-repo/

# 3. Apply main.py additions (see apps/api/main-additions.md)

# 4. Apply Sidebar additions (see apps/web/components/shared/SidebarPhase3.md)

# 5. Restart + add Celery Beat service
celery -A workers.celery_app beat --loglevel=info
```

---

## Deployment

| Service | Platform | Config |
|---|---|---|
| Frontend | Vercel | Root dir: `apps/web`, auto-deploy on push |
| API | Railway | `apps/api/Dockerfile` + `railway.toml` |
| Worker | Railway | Same Dockerfile, `celery worker` command |
| Beat | Railway | Same Dockerfile, `celery beat` command |
| Redis | Railway | Add Redis plugin |
| DB | Supabase | Managed PostgreSQL |
| Email | Resend | API key in env |

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python 3.12) |
| Database | Supabase (PostgreSQL + Realtime) |
| Auth | Clerk |
| Queue | Redis + Celery |
| Email | Resend |
| Charts | Recharts |
