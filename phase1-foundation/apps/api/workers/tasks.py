"""
Celery tasks — background webhook processing.
Called by webhook router after HTTP 200 is returned to provider.
"""
import asyncio
import logging
from datetime import datetime, timezone
from workers.celery_app import celery_app
from database import get_sync_db
from adapters.billing.lemon_squeezy import LemonSqueezyAdapter
from adapters.billing.paddle import PaddleAdapter

logger = logging.getLogger(__name__)

BILLING_ADAPTERS = {
    "lemon_squeezy": LemonSqueezyAdapter(),
    "paddle":        PaddleAdapter(),
}


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=3600,
    name="tasks.process_webhook_event",
)
def process_webhook_event(
    self,
    provider: str,
    workspace_id: str,
    db_event_id: str,
    payload: dict,
):
    """
    Core processing pipeline:
    1. Normalize billing event via adapter
    2. Load community integration
    3. Run automation engine (grant/revoke access)
    4. Queue dunning emails if payment failed
    5. Mark webhook processed
    """
    db = get_sync_db()

    try:
        # Mark as processing
        db.table("webhook_events").update(
            {"status": "processing"}
        ).eq("id", db_event_id).execute()

        # Normalize event
        adapter = BILLING_ADAPTERS.get(provider)
        if not adapter:
            raise ValueError(f"No adapter for provider: {provider}")
        event = adapter.normalize_event(payload)

        # Load active community integration for this workspace
        ci_resp = (
            db.table("community_integrations")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if not ci_resp.data:
            logger.warning(f"No community integration for workspace {workspace_id}")
            db.table("webhook_events").update({
                "status": "skipped",
                "error_message": "No active community integration",
            }).eq("id", db_event_id).execute()
            return

        ci = ci_resp.data[0]

        # Build community adapter
        if ci["platform"] == "circle":
            from adapters.community.circle import CircleAdapter
            community_adapter = CircleAdapter(
                api_key=ci["api_key_enc"],
                community_id=ci["community_id"],
            )
        else:
            raise ValueError(f"Unsupported platform: {ci['platform']}")

        # Run automation engine
        from services.automation_engine import AutomationEngine
        from services.audit_service import AuditService
        audit  = AuditService(db)
        engine = AutomationEngine(db, community_adapter, audit)
        asyncio.run(engine.process_event(workspace_id, event, db_event_id))

        # Queue dunning emails for failed payments
        from services.dunning_service import DunningService
        dunning = DunningService(db)
        asyncio.run(dunning.handle_event(workspace_id, event))

        # Mark processed
        db.table("webhook_events").update({
            "status":       "processed",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "retry_count":  self.request.retries,
        }).eq("id", db_event_id).execute()

        logger.info(f"Processed webhook {db_event_id} ({event.event_type.value})")

    except Exception as exc:
        db.table("webhook_events").update({
            "status":        "failed",
            "error_message": str(exc),
            "retry_count":   self.request.retries,
        }).eq("id", db_event_id).execute()
        raise
