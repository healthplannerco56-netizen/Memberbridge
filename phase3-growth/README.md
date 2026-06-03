# Phase 3 — Growth

Adds dunning system, email automation, analytics, and production hardening.
Drop these files into your Phase 1+2 repo.

## What's added

| Area | Files |
|---|---|
| Dunning service | `apps/api/services/dunning_service.py` |
| Email service | `apps/api/services/email_service.py` |
| Dunning router | `apps/api/routers/dunning.py` |
| Scheduled tasks | `apps/api/workers/scheduled.py` |
| Dunning page | `apps/web/app/dashboard/dunning/page.tsx` |
| Analytics page | `apps/web/app/dashboard/analytics/page.tsx` |
| Analytics components | `apps/web/components/analytics/` |

## Migration needed

Run `supabase/migrations/002_analytics.sql` in Supabase SQL editor before deploying.
