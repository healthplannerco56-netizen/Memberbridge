"""
Clerk JWT verification middleware.

workspace_id resolution order:
  1. JWT public_metadata.workspace_id  (fast path, after first login post-creation)
  2. DB lookup by clerk_user_id        (fallback for brand-new users whose JWT
                                        hasn't refreshed yet after workspace creation)
"""
import logging
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from supabase import AsyncClient

from config import settings
from database import get_db

logger = logging.getLogger(__name__)


class AuthenticatedUser:
    def __init__(self, clerk_user_id: str, workspace_id: str):
        self.clerk_user_id = clerk_user_id
        self.workspace_id  = workspace_id


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncClient = Depends(get_db),
) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(
            token,
            settings.clerk_secret_key,
            algorithms=["RS256", "HS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    # Fast path: workspace_id already in JWT metadata
    workspace_id = payload.get("public_metadata", {}).get("workspace_id", "")

    # Fallback: look up from DB (new users whose JWT hasn't refreshed yet)
    if not workspace_id:
        resp = (
            await db.table("workspaces")
            .select("id")
            .eq("clerk_user_id", clerk_user_id)
            .maybe_single()
            .execute()
        )
        if resp.data:
            workspace_id = resp.data["id"]

    return AuthenticatedUser(
        clerk_user_id=clerk_user_id,
        workspace_id=workspace_id,
    )


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
