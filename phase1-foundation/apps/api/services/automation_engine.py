"""
Automation rule engine.
Evaluates rules against normalized billing events and executes
community platform actions (grant/revoke/role-change).
"""
import logging
from typing import Any
from supabase import Client, AsyncClient
from adapters.billing.base import NormalizedBillingEvent, BillingEventType
from adapters.community.base import CommunityAdapter
from services.audit_service import AuditService

logger = logging.getLogger(__name__)

STATUS_TO_ACCESS = {
    "active":    "active",
    "trialing":  "trialing",
    "past_due":  "past_due",
    "cancelled": "cancelled",
    "expired":   "inactive",
    "paused":    "inactive",
}


class AutomationEngine:

    def __init__(self, db: Client | AsyncClient,
                 community: CommunityAdapter, audit: AuditService):
        self.db        = db
        self.community = community
        self.audit     = audit

    async def process_event(
        self, workspace_id: str, event: NormalizedBillingEvent, webhook_event_id: str
    ) -> list[dict]:
        if not event.customer_email:
            raise ValueError(f"No customer email in event {event.provider_event_id}")

        member = await self._upsert_member(workspace_id, event)
        await self._upsert_subscription(workspace_id, member["id"], event)
        rules  = await self._load_rules(workspace_id, event.event_type)

        results = []
        for rule in rules:
            result = await self._execute_rule(
                workspace_id, rule, event, member, webhook_event_id
            )
            results.append(result)
        return results

    # ── Private helpers ─────────────────────────────────────────

    async def _upsert_member(self, workspace_id: str, event: NormalizedBillingEvent) -> dict:
        access_status = STATUS_TO_ACCESS.get(event.subscription_status, "inactive")
        resp = await self.db.table("members").upsert(
            {
                "workspace_id":       workspace_id,
                "email":              event.customer_email,
                "name":               event.customer_name,
                "billing_customer_id":event.provider_customer_id,
                "billing_provider":   event.provider,
                "access_status":      access_status,
            },
            on_conflict="workspace_id,email",
        ).execute()
        return resp.data[0]

    async def _upsert_subscription(
        self, workspace_id: str, member_id: str, event: NormalizedBillingEvent
    ) -> dict:
        resp = await self.db.table("subscriptions").upsert(
            {
                "workspace_id":          workspace_id,
                "member_id":             member_id,
                "billing_provider":      event.provider,
                "provider_sub_id":       event.provider_subscription_id,
                "provider_plan_id":      event.provider_plan_id,
                "provider_customer_id":  event.provider_customer_id,
                "status":                event.subscription_status,
                "current_period_start":  event.current_period_start.isoformat()
                                         if event.current_period_start else None,
                "current_period_end":    event.current_period_end.isoformat()
                                         if event.current_period_end else None,
                "trial_ends_at":         event.trial_ends_at.isoformat()
                                         if event.trial_ends_at else None,
                "cancelled_at":          event.cancelled_at.isoformat()
                                         if event.cancelled_at else None,
                "amount":                event.amount,
                "currency":              event.currency,
            },
            on_conflict="billing_provider,provider_sub_id",
        ).execute()
        return resp.data[0]

    async def _load_rules(
        self, workspace_id: str, event_type: BillingEventType
    ) -> list[dict]:
        resp = await self.db.table("automation_rules").select("*").eq(
            "workspace_id", workspace_id
        ).eq("trigger_event", event_type.value).eq("is_active", True).order("priority").execute()
        return resp.data

    async def _execute_rule(
        self, workspace_id: str, rule: dict,
        event: NormalizedBillingEvent, member: dict, webhook_event_id: str,
    ) -> dict:
        rec = {
            "workspace_id":    workspace_id,
            "rule_id":         rule["id"],
            "webhook_event_id":webhook_event_id,
            "member_id":       member["id"],
            "trigger_event":   event.event_type.value,
            "action_type":     rule["action_type"],
            "status":          "pending",
        }
        try:
            result = await self._dispatch(rule["action_type"], rule.get("action_config", {}), event, member)
            rec["status"] = "success"
            rec["result"] = result
            await self.audit.log(workspace_id=workspace_id, actor_type="system",
                                 action=f"automation.{rule['action_type']}",
                                 resource_type="member", resource_id=member["id"],
                                 metadata={"rule_id": rule["id"], "result": result})
        except Exception as e:
            logger.exception(f"Rule {rule['id']} failed: {e}")
            rec["status"]        = "failed"
            rec["error_message"] = str(e)

        await self.db.table("automation_executions").insert(rec).execute()
        return rec

    async def _dispatch(
        self, action_type: str, config: dict,
        event: NormalizedBillingEvent, member: dict,
    ) -> dict:
        if action_type == "grant_access":
            return await self._grant_access(config, event, member)
        if action_type == "revoke_access":
            return await self._revoke_access(config, event, member)
        if action_type == "change_role":
            return await self._change_role(config, event, member)
        raise ValueError(f"Unknown action_type: {action_type}")

    async def _grant_access(self, config, event, member):
        existing = await self.community.get_member_by_email(event.customer_email)
        if existing:
            if role := config.get("role"):
                await self.community.change_member_role(existing.platform_user_id, role)
            return {"action": "role_updated", "community_user_id": existing.platform_user_id}

        new_m = await self.community.invite_member(
            email=event.customer_email, name=event.customer_name,
            role=config.get("role"), space_ids=config.get("space_ids"),
        )
        await self.db.table("members").update({
            "community_user_id": new_m.platform_user_id,
            "community_platform": self.community.platform_name,
        }).eq("id", member["id"]).execute()
        return {"action": "invited", "community_user_id": new_m.platform_user_id}

    async def _revoke_access(self, config, event, member):
        cuid = member.get("community_user_id")
        if not cuid:
            found = await self.community.get_member_by_email(event.customer_email)
            if found: cuid = found.platform_user_id
        if not cuid:
            return {"action": "skipped", "reason": "member not in community"}

        space_ids = config.get("space_ids")
        if space_ids:
            await self.community.remove_member_from_spaces(cuid, space_ids)
            return {"action": "spaces_removed", "community_user_id": cuid}
        await self.community.remove_member(cuid)
        return {"action": "removed", "community_user_id": cuid}

    async def _change_role(self, config, event, member):
        cuid = member.get("community_user_id")
        if not cuid:
            return {"action": "skipped", "reason": "no community_user_id"}
        new_role = config.get("role", "member")
        await self.community.change_member_role(cuid, new_role)
        return {"action": "role_changed", "new_role": new_role}
