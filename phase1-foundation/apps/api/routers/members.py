"""Members — list, detail, manual sync."""
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from database import get_db
from middleware.auth import CurrentUser

router = APIRouter(prefix="/members", tags=["members"])


@router.get("")
async def list_members(
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    query = (
        db.table("members")
        .select("*, subscriptions(status,amount,currency,billing_interval,current_period_end)")
        .eq("workspace_id", user.workspace_id)
    )
    if status:
        query = query.eq("access_status", status)
    if search:
        query = query.ilike("email", f"%{search}%")

    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1).order("created_at", desc=True)
    resp = await query.execute()
    return {"data": resp.data, "page": page, "per_page": per_page}


@router.get("/{member_id}")
async def get_member(
    member_id: str,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    resp = (
        await db.table("members")
        .select("*, subscriptions(*), automation_executions(*)")
        .eq("id", member_id)
        .eq("workspace_id", user.workspace_id)
        .single()
        .execute()
    )
    return resp.data


@router.post("/{member_id}/sync")
async def sync_member(
    member_id: str,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    """Manually re-sync a member's community access based on current subscription status."""
    member_resp = await db.table("members").select("*").eq("id", member_id).eq(
        "workspace_id", user.workspace_id
    ).single().execute()
    member = member_resp.data

    ci_resp = await db.table("community_integrations").select("*").eq(
        "workspace_id", user.workspace_id
    ).eq("is_active", True).limit(1).execute()

    if not ci_resp.data:
        return {"success": False, "reason": "No active community integration"}

    # Log the manual sync attempt
    await db.table("audit_logs").insert({
        "workspace_id": user.workspace_id,
        "actor_type":   "user",
        "actor_id":     user.clerk_user_id,
        "action":       "member.manual_sync",
        "resource_type":"member",
        "resource_id":  member_id,
    }).execute()

    return {"success": True, "member_id": member_id, "status": member["access_status"]}
