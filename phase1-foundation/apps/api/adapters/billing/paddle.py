"""
Paddle billing adapter (Paddle Billing / v2).
Docs: https://developer.paddle.com/webhooks/overview
Signature: Paddle-Signature header, format ts=...;h1=...
"""
import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Any
from .base import BillingAdapter, BillingEventType, NormalizedBillingEvent

PADDLE_EVENT_MAP: dict[str, BillingEventType] = {
    "subscription.created":   BillingEventType.SUBSCRIPTION_CREATED,
    "subscription.updated":   BillingEventType.SUBSCRIPTION_UPDATED,
    "subscription.activated": BillingEventType.SUBSCRIPTION_ACTIVE,
    "subscription.paused":    BillingEventType.SUBSCRIPTION_PAUSED,
    "subscription.resumed":   BillingEventType.SUBSCRIPTION_RESUMED,
    "subscription.cancelled": BillingEventType.SUBSCRIPTION_CANCELLED,
    "transaction.completed":  BillingEventType.PAYMENT_SUCCEEDED,
    "transaction.payment_failed": BillingEventType.PAYMENT_FAILED,
}

PADDLE_STATUS_MAP: dict[str, str] = {
    "active":    "active",
    "trialing":  "trialing",
    "past_due":  "past_due",
    "paused":    "paused",
    "cancelled": "cancelled",
}


class PaddleAdapter(BillingAdapter):

    @property
    def provider_name(self) -> str:
        return "paddle"

    def verify_webhook_signature(
        self, payload_bytes: bytes, signature_header: str, secret: str
    ) -> bool:
        """
        Paddle format: Paddle-Signature: ts=<timestamp>;h1=<hmac_sha256>
        Signed payload: <timestamp>:<raw_body>
        """
        try:
            parts = dict(p.split("=", 1) for p in signature_header.split(";"))
            ts = parts.get("ts", "")
            h1 = parts.get("h1", "")
        except Exception:
            return False

        # Reject timestamps older than 5 minutes
        try:
            if abs(time.time() - int(ts)) > 300:
                return False
        except ValueError:
            return False

        signed_payload = f"{ts}:{payload_bytes.decode('utf-8')}".encode()
        expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, h1)

    def get_event_id(self, payload: dict[str, Any]) -> str:
        return payload.get("notification_id") or payload.get("event_id", "")

    def get_event_type(self, payload: dict[str, Any]) -> BillingEventType:
        event_type = payload.get("event_type", "")
        return PADDLE_EVENT_MAP.get(event_type, BillingEventType.UNKNOWN)

    def normalize_event(self, payload: dict[str, Any]) -> NormalizedBillingEvent:
        data = payload.get("data", {})
        customer = data.get("customer", {}) or {}

        def parse_dt(val: str | None) -> datetime | None:
            if not val:
                return None
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None

        status = data.get("status", "")
        # Get price from items if available
        amount = None
        currency = None
        items = data.get("items", [])
        if items:
            price = items[0].get("price", {})
            raw_amount = price.get("unit_price", {}).get("amount")
            if raw_amount:
                amount = int(raw_amount) / 100
            currency = price.get("unit_price", {}).get("currency_code", "USD")

        return NormalizedBillingEvent(
            event_type               = self.get_event_type(payload),
            provider                 = "paddle",
            provider_event_id        = self.get_event_id(payload),
            provider_subscription_id = data.get("id", ""),
            provider_customer_id     = data.get("customer_id", ""),
            provider_plan_id         = data.get("items", [{}])[0].get("price_id") if items else None,
            customer_email           = customer.get("email"),
            customer_name            = customer.get("name"),
            amount                   = amount,
            currency                 = currency,
            subscription_status      = PADDLE_STATUS_MAP.get(status, status),
            current_period_start     = parse_dt(data.get("current_billing_period", {}).get("starts_at")),
            current_period_end       = parse_dt(data.get("current_billing_period", {}).get("ends_at")),
            trial_ends_at            = parse_dt(data.get("trial_dates", {}).get("ends_at")),
            cancelled_at             = parse_dt(data.get("cancelled_at")),
            raw_payload              = payload,
            occurred_at              = parse_dt(payload.get("occurred_at"))
                                       or datetime.now(timezone.utc),
        )
