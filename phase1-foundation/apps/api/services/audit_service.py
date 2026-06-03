"""Writes immutable audit log entries."""
from typing import Any
from supabase import Client, AsyncClient


class AuditService:
    def __init__(self, db: Client | AsyncClient):
        self.db = db

    async def log(
        self,
        workspace_id: str,
        actor_type: str,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor_id: str = "system",
    ):
        entry = {
            "workspace_id":  workspace_id,
            "actor_type":    actor_type,
            "actor_id":      actor_id,
            "action":        action,
            "resource_type": resource_type,
            "resource_id":   resource_id,
            "metadata":      metadata or {},
        }
        if hasattr(self.db, "table"):
            await self.db.table("audit_logs").insert(entry).execute()
