"""
Analytics service.
Computes and stores daily snapshots for dashboard charts.
Called by the nightly Celery beat task.
"""
import logging
from datetime import date, timedelta
from supabase import Client

logger = logging.getLogger(__name__)


class AnalyticsService:

    def __init__(self, db: Client):
        self.db = db

    async def take_snapshot(self, workspace_id: str, snapshot_date: date | None = None) -> dict:
        """Compute and store a daily analytics snapshot for a workspace."""
        d = snapshot_date or date.today()

        active    = await self._count(workspace_id, "access_status", "active")
        past_due  = await self._count(workspace_id, "access_status", "past_due")
        cancelled = await self._count(workspace_id, "access_status", "cancelled")

        # New members today
        today_start = f"{d.isoformat()}T00:00:00+00:00"
        tomorrow    = (d + timedelta(days=1)).isoformat()
        new_resp = await self.db.table("members").select(
            "id", count="exact"
        ).eq("workspace_id", workspace_id).gte(
            "created_at", today_start
        ).lt("created_at", f"{tomorrow}T00:00:00+00:00").execute()
        new_count = new_resp.count or 0

        # MRR estimate (sum of monthly-equivalent amounts for active subs)
        mrr_resp = await self.db.table("subscriptions").select(
            "amount,billing_interval"
        ).eq("workspace_id", workspace_id).eq("status", "active").execute()

        mrr = 0.0
        for s in mrr_resp.data:
            amt = s.get("amount") or 0
            interval = s.get("billing_interval") or "month"
            if interval == "year":
                mrr += amt / 12
            else:
                mrr += amt

        snapshot = {
            "workspace_id":   workspace_id,
            "date":           d.isoformat(),
            "active_count":   active,
            "past_due_count": past_due,
            "cancelled_count":cancelled,
            "new_members":    new_count,
            "mrr":            round(mrr, 2),
        }

        await self.db.table("analytics_snapshots").upsert(
            snapshot, on_conflict="workspace_id,date"
        ).execute()

        return snapshot

    async def get_trend(self, workspace_id: str, days: int = 30) -> list[dict]:
        """Fetch last N days of snapshots for charting."""
        since = (date.today() - timedelta(days=days)).isoformat()
        resp  = await self.db.table("analytics_snapshots").select("*").eq(
            "workspace_id", workspace_id
        ).gte("date", since).order("date").execute()
        return resp.data

    async def _count(self, workspace_id: str, field: str, value: str) -> int:
        resp = await self.db.table("members").select(
            "id", count="exact"
        ).eq("workspace_id", workspace_id).eq(field, value).execute()
        return resp.count or 0
