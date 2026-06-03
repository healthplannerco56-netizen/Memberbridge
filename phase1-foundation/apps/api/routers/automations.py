"""Automation rules — CRUD + execution log."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from supabase import AsyncClient
from database import get_db
from middleware.auth import CurrentUser

router = APIRouter(prefix="/automations", tags=["automations"])


class RuleCreate(BaseModel):
    name: str
    trigger_event: str
    action_type: str
    action_config: dict = {}
    trigger_conditions: dict = {}
    priority: int = 100


class RuleUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    action_config: dict | None = None
    priority: int | None = None


@router.get("")
async def list_rules(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    resp = await db.table("automation_rules").select("*").eq(
        "workspace_id", user.workspace_id
    ).order("priority").execute()
    return resp.data


@router.post("", status_code=201)
async def create_rule(
    body: RuleCreate, user: CurrentUser, db: AsyncClient = Depends(get_db)
):
    resp = await db.table("automation_rules").insert({
        "workspace_id":        user.workspace_id,
        "name":                body.name,
        "trigger_event":       body.trigger_event,
        "action_type":         body.action_type,
        "action_config":       body.action_config,
        "trigger_conditions":  body.trigger_conditions,
        "priority":            body.priority,
    }).execute()
    return resp.data[0]


@router.patch("/{rule_id}")
async def update_rule(
    rule_id: str,
    body: RuleUpdate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    resp = await db.table("automation_rules").update(updates).eq(
        "id", rule_id
    ).eq("workspace_id", user.workspace_id).execute()
    return resp.data[0]


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: str, user: CurrentUser, db: AsyncClient = Depends(get_db)
):
    await db.table("automation_rules").delete().eq("id", rule_id).eq(
        "workspace_id", user.workspace_id
    ).execute()


@router.get("/executions")
async def list_executions(
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=200),
):
    offset = (page - 1) * per_page
    resp = await db.table("automation_executions").select(
        "*, members(email,name), automation_rules(name)"
    ).eq("workspace_id", user.workspace_id).order(
        "executed_at", desc=True
    ).range(offset, offset + per_page - 1).execute()
    return {"data": resp.data, "page": page, "per_page": per_page}
