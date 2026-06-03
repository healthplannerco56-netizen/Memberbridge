"""Abstract billing adapter — all providers implement this interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class BillingEventType(str, Enum):
    SUBSCRIPTION_CREATED  = "subscription.created"
    SUBSCRIPTION_ACTIVE   = "subscription.active"
    SUBSCRIPTION_UPDATED  = "subscription.updated"
    SUBSCRIPTION_PAUSED   = "subscription.paused"
    SUBSCRIPTION_RESUMED  = "subscription.resumed"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_EXPIRED  = "subscription.expired"
    PAYMENT_SUCCEEDED     = "payment.succeeded"
    PAYMENT_FAILED        = "payment.failed"
    TRIAL_ENDED           = "trial.ended"
    UNKNOWN               = "unknown"


@dataclass
class NormalizedBillingEvent:
    """Provider-agnostic billing event used by the automation engine."""
    event_type:               BillingEventType
    provider:                 str
    provider_event_id:        str
    provider_subscription_id: str
    provider_customer_id:     str
    provider_plan_id:         str | None
    customer_email:           str | None
    customer_name:            str | None
    amount:                   float | None
    currency:                 str | None
    subscription_status:      str
    current_period_start:     datetime | None
    current_period_end:       datetime | None
    trial_ends_at:            datetime | None
    cancelled_at:             datetime | None
    raw_payload:              dict[str, Any]
    occurred_at:              datetime


class BillingAdapter(ABC):
    """Implement this for each billing provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def verify_webhook_signature(
        self, payload_bytes: bytes, signature_header: str, secret: str
    ) -> bool: ...

    @abstractmethod
    def get_event_id(self, payload: dict[str, Any]) -> str: ...

    @abstractmethod
    def get_event_type(self, payload: dict[str, Any]) -> BillingEventType: ...

    @abstractmethod
    def normalize_event(self, payload: dict[str, Any]) -> NormalizedBillingEvent: ...
