"""Webhook event log — list, detail, retry."""
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import AsyncClient
from database import get_db
from middleware.auth import CurrentUser

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events(
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
    status: str | None = Query(None),
    provider: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=200),
):
    query = db.table("webhook_events").select("*").eq("workspace_id", user.workspace_id)
    if status:
        query = query.eq("status", status)
    if provider:
        query = query.eq("billing_provider", provider)
    offset = (page - 1) * per_page
    resp = await query.order("created_at", desc=True).range(offset, offset + per_page - 1).execute()
    return {"data": resp.data, "page": page, "per_page": per_page}


@router.get("/{event_id}")
async def get_event(
    event_id: str, user: CurrentUser, db: AsyncClient = Depends(get_db)
):
    resp = await db.table("webhook_events").select("*").eq(
        "id", event_id
    ).eq("workspace_id", user.workspace_id).single().execute()
    return resp.data


@router.post("/{event_id}/retry")
async def retry_event(
    event_id: str, user: CurrentUser, db: AsyncClient = Depends(get_db)
):
    """Re-enqueue a failed webhook event for processing."""
    resp = await db.table("webhook_events").select("*").eq(
        "id", event_id
    ).eq("workspace_id", user.workspace_id).single().execute()
    event = resp.data

    if event["status"] not in ("failed", "skipped"):
        raise HTTPException(status_code=400, detail="Only failed/skipped events can be retried")

    await db.table("webhook_events").update({"status": "received", "error_message": None}).eq(
        "id", event_id
    ).execute()

    from workers.tasks import process_webhook_event
    process_webhook_event.delay(
        provider=event["billing_provider"],
        workspace_id=user.workspace_id,
        db_event_id=event_id,
        payload=event["payload"],
    )
    return {"status": "requeued", "event_id": event_id}
