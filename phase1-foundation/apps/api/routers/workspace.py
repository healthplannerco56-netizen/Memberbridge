"""
Workspace CRUD.
On creation: seeds default automation rules and updates
Clerk public_metadata with workspace_id so it appears in JWTs.
"""
import os
import re
import secrets
import logging

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from supabase import AsyncClient

from database import get_db
from middleware.auth import CurrentUser

router = APIRouter(prefix="/workspace", tags=["workspace"])
logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", text.lower().strip()).strip("-")


async def _set_clerk_metadata(clerk_user_id: str, workspace_id: str) -> None:
    """
    Update Clerk user's public_metadata.workspace_id so it appears
    in their JWT on next token refresh.
    Docs: https://clerk.com/docs/reference/backend-api/tag/Users
    """
    clerk_secret = os.getenv("CLERK_SECRET_KEY", "")
    if not clerk_secret:
        logger.warning("CLERK_SECRET_KEY not set — skipping metadata update")
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.patch(
                f"https://api.clerk.com/v1/users/{clerk_user_id}",
                headers={
                    "Authorization": f"Bearer {clerk_secret}",
                    "Content-Type":  "application/json",
                },
                json={"public_metadata": {"workspace_id": workspace_id}},
            )
            resp.raise_for_status()
            logger.info(f"Clerk metadata updated for {clerk_user_id}")
    except Exception as e:
        # Non-fatal — DB fallback in auth.py handles the gap
        logger.warning(f"Clerk metadata update failed: {e}")


async def _create_default_rules(db: AsyncClient, workspace_id: str) -> None:
    """Seed 4 standard automation rules for every new workspace."""
    defaults = [
        {
            "workspace_id":  workspace_id,
            "name":          "Grant access on payment",
            "trigger_event": "subscription.active",
            "action_type":   "grant_access",
            "action_config": {"role": "member"},
            "priority":      10,
        },
        {
            "workspace_id":  workspace_id,
            "name":          "Grant access on subscription created",
            "trigger_event": "subscription.created",
            "action_type":   "grant_access",
            "action_config": {"role": "member"},
            "priority":      10,
        },
        {
            "workspace_id":  workspace_id,
            "name":          "Revoke access on cancellation",
            "trigger_event": "subscription.cancelled",
            "action_type":   "revoke_access",
            "action_config": {},
            "priority":      10,
        },
        {
            "workspace_id":  workspace_id,
            "name":          "Downgrade role on trial end",
            "trigger_event": "trial.ended",
            "action_type":   "change_role",
            "action_config": {"role": "free_member"},
            "priority":      10,
        },
    ]
    await db.table("automation_rules").insert(defaults).execute()


# ── Pydantic schemas ─────────────────────────────────────────────

class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceUpdate(BaseModel):
    name: str | None = None


# ── Routes ───────────────────────────────────────────────────────

@router.get("")
async def get_workspace(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    resp = (
        await db.table("workspaces")
        .select("*")
        .eq("clerk_user_id", user.clerk_user_id)
        .maybe_single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return resp.data


@router.post("", status_code=201)
async def create_workspace(
    body: WorkspaceCreate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    slug = slugify(body.name)
    existing_slug = await db.table("workspaces").select("id").eq("slug", slug).execute()
    if existing_slug.data:
        slug = f"{slug}-{secrets.token_hex(3)}"

    resp = (
        await db.table("workspaces")
        .insert({
            "clerk_user_id": user.clerk_user_id,
            "name":          body.name,
            "slug":          slug,
        })
        .execute()
    )
    workspace = resp.data[0]
    await _create_default_rules(db, workspace["id"])
    await _set_clerk_metadata(user.clerk_user_id, workspace["id"])
    return workspace


@router.patch("")
async def update_workspace(
    body: WorkspaceUpdate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    resp = (
        await db.table("workspaces")
        .update(updates)
        .eq("clerk_user_id", user.clerk_user_id)
        .execute()
    )
    return resp.data[0]


@router.post("/onboarding-complete")
async def complete_onboarding(
    user: CurrentUser, db: AsyncClient = Depends(get_db)
):
    await db.table("workspaces").update(
        {"onboarding_done": True}
    ).eq("clerk_user_id", user.clerk_user_id).execute()
    return {"success": True}


# ── Internal: called by Clerk webhook (Next.js → FastAPI) ────────

@router.post("/init", status_code=201, include_in_schema=False)
async def init_workspace(
    body: dict,
    db: AsyncClient = Depends(get_db),
    x_service_key: str | None = Header(None),
):
    """
    Called by apps/web/app/api/clerk-webhook/route.ts when a new
    Clerk user is created. Creates workspace + seeds rules + sets
    Clerk public_metadata.workspace_id.
    """
    expected = os.getenv("INTERNAL_SERVICE_KEY", "")
    if expected and x_service_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    clerk_user_id = body.get("clerk_user_id")
    name          = body.get("name", "My Community")
    if not clerk_user_id:
        raise HTTPException(status_code=400, detail="clerk_user_id required")

    # Idempotent — safe to call multiple times
    existing = (
        await db.table("workspaces")
        .select("id")
        .eq("clerk_user_id", clerk_user_id)
        .maybe_single()
        .execute()
    )
    if existing.data:
        return existing.data

    slug = slugify(name)
    slug_exists = await db.table("workspaces").select("id").eq("slug", slug).execute()
    if slug_exists.data:
        slug = f"{slug}-{secrets.token_hex(3)}"

    resp = (
        await db.table("workspaces")
        .insert({
            "clerk_user_id": clerk_user_id,
            "name":          name,
            "slug":          slug,
        })
        .execute()
    )
    workspace = resp.data[0]
    await _create_default_rules(db, workspace["id"])
    await _set_clerk_metadata(clerk_user_id, workspace["id"])
    return workspace
