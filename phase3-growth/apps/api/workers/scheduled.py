"""
Celery Beat scheduled tasks — Phase 3.
Add to celery_app.conf.beat_schedule after importing.
"""
import logging
from datetime import datetime, timezone, timedelta
from workers.celery_app import celery_app
from database import get_sync_db

logger = logging.getLogger(__name__)


# ── Register beat schedule ───────────────────────────────────────
celery_app.conf.beat_schedule.update({
    "send-due-dunning-emails": {
        "task":     "scheduled.send_due_dunning_emails",
        "schedule": 300,   # every 5 minutes
    },
    "nightly-analytics-snapshot": {
        "task":     "scheduled.nightly_analytics_snapshot",
        "schedule": 86400, # every 24 hours
    },
})


@celery_app.task(name="scheduled.send_due_dunning_emails")
def send_due_dunning_emails():
    """
    Poll dunning_email_log for queued emails whose scheduled_for <= now
    and send them via Resend.
    """
    import asyncio
    db  = get_sync_db()
    now = datetime.now(timezone.utc).isoformat()

    due = db.table("dunning_email_log").select(
        "*, subscriptions(member_id, provider_sub_id, billing_provider, "
        "workspace_id), members(email, name)"
    ).eq("status", "queued").lte("scheduled_for", now).limit(50).execute()

    if not due.data:
        return {"sent": 0}

    sent = 0
    for row in due.data:
        try:
            asyncio.run(_send_dunning_email(db, row))
            sent += 1
        except Exception as e:
            logger.error(f"Dunning email {row['id']} failed: {e}")
            db.table("dunning_email_log").update({
                "status": "failed"
            }).eq("id", row["id"]).execute()

    logger.info(f"Dunning: sent {sent}/{len(due.data)} emails")
    return {"sent": sent}


async def _send_dunning_email(db, row: dict):
    """Send a single dunning email and update the log."""
    from services.email_service import EmailService

    sub  = row.get("subscriptions") or {}
    # Resolve workspace + community name
    wid  = sub.get("workspace_id") or row.get("workspace_id")
    ci_resp = db.table("community_integrations").select(
        "community_name"
    ).eq("workspace_id", wid).eq("is_active", True).limit(1).execute()
    community_name = (ci_resp.data[0].get("community_name") if ci_resp.data else None) or "your community"

    member      = row.get("members") or {}
    member_name = member.get("name")
    email       = row["email"]
    step        = row["step_number"]

    svc = EmailService()
    subject, html = svc.render_failed_payment(member_name, community_name, step)
    message_id    = await svc.send(to=email, subject=subject, html=html)

    db.table("dunning_email_log").update({
        "status":            "sent",
        "resend_message_id": message_id,
        "sent_at":           datetime.now(timezone.utc).isoformat(),
    }).eq("id", row["id"]).execute()


@celery_app.task(name="scheduled.nightly_analytics_snapshot")
def nightly_analytics_snapshot():
    """
    Take a daily analytics snapshot for every workspace.
    Runs once per day via Celery Beat.
    """
    import asyncio
    db = get_sync_db()

    workspaces = db.table("workspaces").select("id").execute()
    count = 0
    for ws in workspaces.data:
        try:
            from services.analytics_service import AnalyticsService
            svc = AnalyticsService(db)
            asyncio.run(svc.take_snapshot(ws["id"]))
            count += 1
        except Exception as e:
            logger.error(f"Snapshot failed for workspace {ws['id']}: {e}")

    logger.info(f"Analytics snapshots taken for {count} workspaces")
    return {"workspaces_snapshotted": count}
