"""
Dunning management endpoints.
View sequences, email log, manual send.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from supabase import AsyncClient
from database import get_db
from middleware.auth import CurrentUser

router = APIRouter(prefix="/dunning", tags=["dunning"])


class SequenceCreate(BaseModel):
    name: str = "Default Dunning"


class StepCreate(BaseModel):
    step_number: int
    delay_hours: int
    email_subject: str
    email_body_html: str


# ── Sequences ────────────────────────────────────────────────────

@router.get("/sequences")
async def list_sequences(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    resp = await db.table("dunning_sequences").select(
        "*, dunning_steps(*)"
    ).eq("workspace_id", user.workspace_id).execute()
    return resp.data


@router.post("/sequences", status_code=201)
async def create_sequence(
    body: SequenceCreate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    resp = await db.table("dunning_sequences").insert({
        "workspace_id": user.workspace_id,
        "name":         body.name,
    }).execute()
    seq = resp.data[0]

    # Seed 3 default steps
    default_steps = [
        {"dunning_sequence_id": seq["id"], "step_number": 1,
         "delay_hours": 0,
         "email_subject": "Action needed: Your payment failed",
         "email_body_html": "<p>Hi, your payment failed. Please update your details.</p>"},
        {"dunning_sequence_id": seq["id"], "step_number": 2,
         "delay_hours": 48,
         "email_subject": "Reminder: Payment still outstanding",
         "email_body_html": "<p>Hi, your payment is still outstanding.</p>"},
        {"dunning_sequence_id": seq["id"], "step_number": 3,
         "delay_hours": 120,
         "email_subject": "Final notice: Access will be cancelled",
         "email_body_html": "<p>Final notice — resolve your payment to keep access.</p>"},
    ]
    await db.table("dunning_steps").insert(default_steps).execute()
    return seq


@router.patch("/sequences/{seq_id}")
async def update_sequence(
    seq_id: str,
    body: SequenceCreate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    resp = await db.table("dunning_sequences").update(
        {"name": body.name}
    ).eq("id", seq_id).eq("workspace_id", user.workspace_id).execute()
    return resp.data[0]


# ── Steps ────────────────────────────────────────────────────────

@router.get("/sequences/{seq_id}/steps")
async def list_steps(
    seq_id: str,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    resp = await db.table("dunning_steps").select("*").eq(
        "dunning_sequence_id", seq_id
    ).order("step_number").execute()
    return resp.data


@router.post("/sequences/{seq_id}/steps", status_code=201)
async def add_step(
    seq_id: str,
    body: StepCreate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    resp = await db.table("dunning_steps").insert({
        "dunning_sequence_id": seq_id,
        "step_number":         body.step_number,
        "delay_hours":         body.delay_hours,
        "email_subject":       body.email_subject,
        "email_body_html":     body.email_body_html,
    }).execute()
    return resp.data[0]


@router.patch("/steps/{step_id}")
async def update_step(
    step_id: str,
    body: StepCreate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    resp = await db.table("dunning_steps").update(
        body.model_dump()
    ).eq("id", step_id).execute()
    return resp.data[0]


@router.delete("/steps/{step_id}", status_code=204)
async def delete_step(
    step_id: str,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    await db.table("dunning_steps").delete().eq("id", step_id).execute()


# ── Email Log ────────────────────────────────────────────────────

@router.get("/log")
async def dunning_log(
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=200),
):
    offset = (page - 1) * per_page
    resp = await db.table("dunning_email_log").select(
        "*, subscriptions(provider_sub_id, billing_provider)"
    ).eq("workspace_id", user.workspace_id).order(
        "created_at", desc=True
    ).range(offset, offset + per_page - 1).execute()
    return {"data": resp.data, "page": page, "per_page": per_page}
