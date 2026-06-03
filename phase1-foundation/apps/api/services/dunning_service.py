"""
Dunning service.
Manages failed-payment email sequences.

Default sequence (hours after first failure):
  Step 1 →   0h  (immediate)
  Step 2 →  48h  (2 days)
  Step 3 → 120h  (5 days) — final notice
"""
import logging
from datetime import datetime, timezone, timedelta
from supabase import Client, AsyncClient
from adapters.billing.base import NormalizedBillingEvent, BillingEventType

logger = logging.getLogger(__name__)

DEFAULT_STEPS = [
    {"step_number": 1, "delay_hours":   0},
    {"step_number": 2, "delay_hours":  48},
    {"step_number": 3, "delay_hours": 120},
]


class DunningService:

    def __init__(self, db: Client | AsyncClient):
        self.db = db

    async def handle_event(
        self, workspace_id: str, event: NormalizedBillingEvent
    ) -> None:
        """Called after automation engine. Handles dunning side-effects."""
        if event.event_type == BillingEventType.PAYMENT_FAILED:
            await self._on_payment_failed(workspace_id, event)
        elif event.event_type in (
            BillingEventType.PAYMENT_SUCCEEDED,
            BillingEventType.SUBSCRIPTION_CANCELLED,
            BillingEventType.SUBSCRIPTION_EXPIRED,
        ):
            await self._cancel_dunning(workspace_id, event.provider_subscription_id)

    async def _on_payment_failed(
        self, workspace_id: str, event: NormalizedBillingEvent
    ) -> None:
        # Fetch or create subscription record
        sub_resp = await self.db.table("subscriptions").select(
            "id,failed_payment_count,dunning_step,last_payment_failed_at"
        ).eq("billing_provider", event.provider).eq(
            "provider_sub_id", event.provider_subscription_id
        ).maybe_single().execute()

        if not sub_resp.data:
            logger.warning(f"Subscription not found for dunning: {event.provider_subscription_id}")
            return

        sub       = sub_resp.data
        now       = datetime.now(timezone.utc)
        new_count = sub["failed_payment_count"] + 1
        new_step  = min(sub["dunning_step"] + 1, len(DEFAULT_STEPS))

        # Update subscription counters
        await self.db.table("subscriptions").update({
            "failed_payment_count":  new_count,
            "dunning_step":          new_step,
            "last_payment_failed_at": now.isoformat(),
            "status":                "past_due",
        }).eq("id", sub["id"]).execute()

        if not event.customer_email:
            return

        # Load active dunning sequence for workspace
        seq_resp = await self.db.table("dunning_sequences").select(
            "id"
        ).eq("workspace_id", workspace_id).eq("is_active", True).limit(1).execute()

        # Schedule the matching step email
        step_config = DEFAULT_STEPS[new_step - 1] if new_step <= len(DEFAULT_STEPS) else None
        if not step_config:
            return

        scheduled_for = now + timedelta(hours=step_config["delay_hours"])

        await self.db.table("dunning_email_log").insert({
            "workspace_id":   workspace_id,
            "subscription_id":sub["id"],
            "step_number":    new_step,
            "email":          event.customer_email,
            "status":         "queued",
            "scheduled_for":  scheduled_for.isoformat(),
        }).execute()

        logger.info(
            f"Dunning step {new_step} queued for {event.customer_email}"
            f" at {scheduled_for.isoformat()}"
        )

    async def _cancel_dunning(self, workspace_id: str, provider_sub_id: str) -> None:
        """Cancel all pending dunning emails when payment recovers or sub ends."""
        sub_resp = await self.db.table("subscriptions").select("id").eq(
            "provider_sub_id", provider_sub_id
        ).maybe_single().execute()

        if not sub_resp.data:
            return

        await self.db.table("dunning_email_log").update(
            {"status": "cancelled"}
        ).eq("subscription_id", sub_resp.data["id"]).eq("status", "queued").execute()

        # Reset dunning step counter
        await self.db.table("subscriptions").update({
            "dunning_step":          0,
            "failed_payment_count":  0,
        }).eq("id", sub_resp.data["id"]).execute()

        logger.info(f"Dunning cancelled for subscription {provider_sub_id}")
