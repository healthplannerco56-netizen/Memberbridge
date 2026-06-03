"""Integration management — billing + community providers."""
import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import AsyncClient
from database import get_db
from middleware.auth import CurrentUser

router = APIRouter(prefix="/integrations", tags=["integrations"])


# ── BILLING ──────────────────────────────────────────────────────

class BillingIntegrationCreate(BaseModel):
    provider: str
    api_key: str
    webhook_secret: str


@router.get("/billing")
async def list_billing(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    resp = await db.table("billing_integrations").select(
        "id,provider,is_active,config,created_at"  # never return encrypted fields
    ).eq("workspace_id", user.workspace_id).execute()
    return resp.data


@router.post("/billing", status_code=201)
async def create_billing(
    body: BillingIntegrationCreate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    # Generate a unique webhook token for this workspace/provider combo
    webhook_token = secrets.token_urlsafe(16)

    resp = (
        await db.table("billing_integrations")
        .upsert(
            {
                "workspace_id":  user.workspace_id,
                "provider":      body.provider,
                "api_key_enc":   body.api_key,      # TODO: encrypt before storing
                "webhook_secret": body.webhook_secret,
                "is_active":     True,
                "config":        {"webhook_token": webhook_token},
            },
            on_conflict="workspace_id,provider",
        )
        .execute()
    )
    integration = resp.data[0]
    # Return webhook URL so the creator can paste it into their provider
    integration["webhook_url"] = (
        f"https://api.memberbridge.io/api/v1/webhooks/{body.provider}/{webhook_token}"
    )
    return integration


@router.delete("/billing/{provider}", status_code=204)
async def delete_billing(
    provider: str, user: CurrentUser, db: AsyncClient = Depends(get_db)
):
    await db.table("billing_integrations").update({"is_active": False}).eq(
        "workspace_id", user.workspace_id
    ).eq("provider", provider).execute()


# ── COMMUNITY ────────────────────────────────────────────────────

class CommunityIntegrationCreate(BaseModel):
    platform: str
    api_key: str
    community_id: str


@router.get("/community")
async def list_community(user: CurrentUser, db: AsyncClient = Depends(get_db)):
    resp = await db.table("community_integrations").select(
        "id,platform,is_active,community_id,community_name,config,created_at"
    ).eq("workspace_id", user.workspace_id).execute()
    return resp.data


@router.post("/community", status_code=201)
async def create_community(
    body: CommunityIntegrationCreate,
    user: CurrentUser,
    db: AsyncClient = Depends(get_db),
):
    # Verify the API key works before saving
    community_name = await _verify_circle(body.api_key, body.community_id)

    resp = (
        await db.table("community_integrations")
        .upsert(
            {
                "workspace_id":  user.workspace_id,
                "platform":      body.platform,
                "api_key_enc":   body.api_key,
                "community_id":  body.community_id,
                "community_name": community_name,
                "is_active":     True,
            },
            on_conflict="workspace_id,platform",
        )
        .execute()
    )
    return resp.data[0]


@router.delete("/community/{platform}", status_code=204)
async def delete_community(
    platform: str, user: CurrentUser, db: AsyncClient = Depends(get_db)
):
    await db.table("community_integrations").update({"is_active": False}).eq(
        "workspace_id", user.workspace_id
    ).eq("platform", platform).execute()


async def _verify_circle(api_key: str, community_id: str) -> str:
    """Test Circle API key by fetching the community name."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://app.circle.so/api/v1/communities/{community_id}",
                headers={"Authorization": f"Token {api_key}"},
            )
            resp.raise_for_status()
            return resp.json().get("name", "Unknown Community")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not verify Circle API key: {str(e)}"
        )
