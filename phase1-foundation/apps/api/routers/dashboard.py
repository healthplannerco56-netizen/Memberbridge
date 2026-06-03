"""Dashboard summary stats."""
from fastapi import APIRouter, Depends
from supabase import AsyncClient
from database import get_db
from middleware.auth import CurrentUser

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    wid = user.workspace_id

    active   = await db.table("members").select("id", count="exact").eq("workspace_id", wid).eq("access_status", "active").execute()
    past_due = await db.table("members").select("id", count="exact").eq("workspace_id", wid).eq("access_status", "past_due").execute()
    cancelled= await db.table("members").select("id", count="exact").eq("workspace_id", wid).eq("access_status", "cancelled").execute()
    failed   = await db.table("webhook_events").select("id", count="exact").eq("workspace_id", wid).eq("status", "failed").execute()

    # Revenue at risk = sum of past_due subscription amounts
    risk_resp = await db.table("subscriptions").select("amount").eq(
        "workspace_id", wid
    ).eq("status", "past_due").execute()
    revenue_at_risk = sum(r.get("amount") or 0 for r in risk_resp.data)

    return {
        "active_members":   active.count or 0,
        "past_due_members": past_due.count or 0,
        "cancelled_members":cancelled.count or 0,
        "failed_events":    failed.count or 0,
        "revenue_at_risk":  round(revenue_at_risk, 2),
    }


@router.get("/recent-events")
async def recent_events(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    resp = await db.table("webhook_events").select("*").eq(
        "workspace_id", user.workspace_id
    ).order("created_at", desc=True).limit(20).execute()
    return resp.data
