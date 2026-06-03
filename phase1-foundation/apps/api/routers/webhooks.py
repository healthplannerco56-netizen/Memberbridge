"""
Webhook receiver endpoints.
Each provider gets a workspace-scoped URL via a unique token.
Flow: verify sig → deduplicate → persist → enqueue → HTTP 200
"""
import json
import logging
import secrets
from typing import Annotated
from fastapi import APIRouter, Header, HTTPException, Request, status
from supabase import AsyncClient
from fastapi import Depends
from database import get_db
from adapters.billing.lemon_squeezy import LemonSqueezyAdapter
from adapters.billing.paddle import PaddleAdapter
from workers.tasks import process_webhook_event

router  = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger  = logging.getLogger(__name__)

ADAPTERS = {
    "lemon_squeezy": LemonSqueezyAdapter(),
    "paddle":        PaddleAdapter(),
}


async def _resolve_workspace(
    db: AsyncClient, provider: str, workspace_token: str
) -> str:
    """Resolve webhook token → workspace_id."""
    resp = (
        await db.table("billing_integrations")
        .select("workspace_id")
        .eq("provider", provider)
        .eq("config->>webhook_token", workspace_token)
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Unknown webhook token")
    return resp.data["workspace_id"]


async def _load_secret(db: AsyncClient, workspace_id: str, provider: str) -> str:
    resp = (
        await db.table("billing_integrations")
        .select("webhook_secret")
        .eq("workspace_id", workspace_id)
        .eq("provider", provider)
        .eq("is_active", True)
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=400, detail="Integration not found or inactive")
    return resp.data["webhook_secret"] or ""


async def _handle(
    provider: str,
    workspace_token: str,
    request: Request,
    db: AsyncClient,
    signature: str | None,
) -> dict:
    body    = await request.body()
    payload = json.loads(body)
    adapter = ADAPTERS[provider]

    workspace_id = await _resolve_workspace(db, provider, workspace_token)
    secret       = await _load_secret(db, workspace_id, provider)

    # Verify signature
    if signature and secret:
        if not adapter.verify_webhook_signature(body, signature, secret):
            logger.warning(f"Bad signature from {provider} for workspace {workspace_id}")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_id   = adapter.get_event_id(payload)
    event_type = adapter.get_event_type(payload).value

    # Idempotency check
    existing = (
        await db.table("webhook_events")
        .select("id,status")
        .eq("billing_provider", provider)
        .eq("provider_event_id", event_id)
        .maybe_single()
        .execute()
    )
    if existing.data and existing.data["status"] in ("processed", "processing"):
        return {"status": "duplicate", "event_id": event_id}

    # Persist raw event
    insert = (
        await db.table("webhook_events")
        .upsert(
            {
                "workspace_id":      workspace_id,
                "billing_provider":  provider,
                "provider_event_id": event_id,
                "event_type":        event_type,
                "payload":           payload,
                "status":            "received",
            },
            on_conflict="billing_provider,provider_event_id",
        )
        .execute()
    )
    db_event_id = insert.data[0]["id"]

    # Enqueue (fire and forget)
    process_webhook_event.delay(
        provider=provider,
        workspace_id=workspace_id,
        db_event_id=db_event_id,
        payload=payload,
    )

    return {"status": "queued", "event_id": event_id}


@router.post("/lemon-squeezy/{workspace_token}")
async def lemon_squeezy_webhook(
    workspace_token: str,
    request: Request,
    db: AsyncClient = Depends(get_db),
    x_signature: Annotated[str | None, Header()] = None,
):
    return await _handle("lemon_squeezy", workspace_token, request, db, x_signature)


@router.post("/paddle/{workspace_token}")
async def paddle_webhook(
    workspace_token: str,
    request: Request,
    db: AsyncClient = Depends(get_db),
    paddle_signature: Annotated[str | None, Header()] = None,
):
    return await _handle("paddle", workspace_token, request, db, paddle_signature)
