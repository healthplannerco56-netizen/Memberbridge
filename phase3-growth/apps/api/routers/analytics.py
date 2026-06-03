"""Analytics endpoints — trend data for dashboard charts."""
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from database import get_db
from middleware.auth import CurrentUser
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/trend")
async def get_trend(
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
    days: int = Query(30, ge=7, le=90),
):
    """Return daily snapshots for member count + MRR charts."""
    svc = AnalyticsService(db)
    return await svc.get_trend(user.workspace_id, days)


@router.post("/snapshot")
async def trigger_snapshot(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    """Manually trigger a snapshot (useful for testing)."""
    svc = AnalyticsService(db)
    return await svc.take_snapshot(user.workspace_id)


@router.get("/mrr-summary")
async def mrr_summary(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    """Current MRR broken down by plan/interval."""
    resp = await db.table("subscriptions").select(
        "amount,billing_interval,provider_plan_id"
    ).eq("workspace_id", user.workspace_id).eq("status", "active").execute()

    monthly = sum(
        (s["amount"] or 0) for s in resp.data if s["billing_interval"] != "year"
    )
    annual_as_monthly = sum(
        (s["amount"] or 0) / 12 for s in resp.data if s["billing_interval"] == "year"
    )
    total_mrr = round(monthly + annual_as_monthly, 2)
    total_arr = round(total_mrr * 12, 2)

    return {
        "mrr":            total_mrr,
        "arr":            total_arr,
        "active_subs":    len(resp.data),
        "monthly_subs":   sum(1 for s in resp.data if s["billing_interval"] != "year"),
        "annual_subs":    sum(1 for s in resp.data if s["billing_interval"] == "year"),
    }
