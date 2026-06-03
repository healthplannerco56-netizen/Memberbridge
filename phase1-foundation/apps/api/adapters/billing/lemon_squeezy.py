"""
Lemon Squeezy billing adapter.
Docs: https://docs.lemonsqueezy.com/api/webhooks
Signature: HMAC-SHA256, header X-Signature
"""
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any
from .base import BillingAdapter, BillingEventType, NormalizedBillingEvent

LS_EVENT_MAP: dict[str, BillingEventType] = {
    "subscription_created":          BillingEventType.SUBSCRIPTION_CREATED,
    "subscription_updated":          BillingEventType.SUBSCRIPTION_UPDATED,
    "subscription_active":           BillingEventType.SUBSCRIPTION_ACTIVE,
    "subscription_paused":           BillingEventType.SUBSCRIPTION_PAUSED,
    "subscription_unpaused":         BillingEventType.SUBSCRIPTION_RESUMED,
    "subscription_cancelled":        BillingEventType.SUBSCRIPTION_CANCELLED,
    "subscription_resumed":          BillingEventType.SUBSCRIPTION_RESUMED,
    "subscription_expired":          BillingEventType.SUBSCRIPTION_EXPIRED,
    "subscription_payment_success":  BillingEventType.PAYMENT_SUCCEEDED,
    "subscription_payment_failed":   BillingEventType.PAYMENT_FAILED,
    "subscription_payment_recovered":BillingEventType.PAYMENT_SUCCEEDED,
    "subscription_trial_started":    BillingEventType.SUBSCRIPTION_CREATED,
}

LS_STATUS_MAP: dict[str, str] = {
    "active":   "active",
    "paused":   "paused",
    "past_due": "past_due",
    "cancelled":"cancelled",
    "expired":  "expired",
    "on_trial": "trialing",
    "unpaid":   "past_due",
}


class LemonSqueezyAdapter(BillingAdapter):

    @property
    def provider_name(self) -> str:
        return "lemon_squeezy"

    def verify_webhook_signature(
        self, payload_bytes: bytes, signature_header: str, secret: str
    ) -> bool:
        expected = hmac.new(
            secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    def get_event_id(self, payload: dict[str, Any]) -> str:
        meta = payload.get("meta", {})
        return str(meta.get("webhook_id") or payload.get("data", {}).get("id", ""))

    def get_event_type(self, payload: dict[str, Any]) -> BillingEventType:
        ls_event = payload.get("meta", {}).get("event_name", "")
        return LS_EVENT_MAP.get(ls_event, BillingEventType.UNKNOWN)

    def normalize_event(self, payload: dict[str, Any]) -> NormalizedBillingEvent:
        meta  = payload.get("meta", {})
        data  = payload.get("data", {})
        attrs = data.get("attributes", {})

        def parse_dt(val: str | None) -> datetime | None:
            if not val:
                return None
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None

        event_type = LS_EVENT_MAP.get(
            meta.get("event_name", ""), BillingEventType.UNKNOWN
        )
        status = attrs.get("status", "")
        trial_ends_at = parse_dt(attrs.get("trial_ends_at")) if status == "on_trial" else None
        cancelled_at  = parse_dt(attrs.get("ends_at")) if attrs.get("cancelled") else None

        return NormalizedBillingEvent(
            event_type               = event_type,
            provider                 = "lemon_squeezy",
            provider_event_id        = self.get_event_id(payload),
            provider_subscription_id = str(data.get("id", "")),
            provider_customer_id     = str(attrs.get("customer_id", "")),
            provider_plan_id         = str(attrs.get("variant_id", "")),
            customer_email           = attrs.get("user_email") or
                                       meta.get("custom_data", {}).get("email"),
            customer_name            = attrs.get("user_name"),
            amount                   = attrs.get("unit_price", 0) / 100,
            currency                 = attrs.get("currency", "USD").upper(),
            subscription_status      = LS_STATUS_MAP.get(status, status),
            current_period_start     = parse_dt(attrs.get("created_at")),
            current_period_end       = parse_dt(attrs.get("renews_at")),
            trial_ends_at            = trial_ends_at,
            cancelled_at             = cancelled_at,
            raw_payload              = payload,
            occurred_at              = parse_dt(attrs.get("updated_at"))
                                       or datetime.now(timezone.utc),
        )
