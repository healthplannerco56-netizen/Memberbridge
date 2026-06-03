// ─── Core domain types ────────────────────────────────────────

export type Plan = "starter" | "pro" | "business";
export type AccessStatus = "active" | "inactive" | "past_due" | "cancelled" | "trialing";
export type SubStatus = "trialing" | "active" | "past_due" | "cancelled" | "expired" | "paused";
export type BillingProvider = "paddle" | "lemon_squeezy" | "stripe" | "paypal";
export type CommunityPlatform = "circle" | "skool" | "mighty_networks";
export type TriggerEvent =
  | "subscription.created" | "subscription.active" | "payment.failed"
  | "subscription.cancelled" | "subscription.expired" | "trial.ended"
  | "subscription.paused"   | "subscription.resumed";
export type ActionType =
  | "grant_access" | "revoke_access" | "change_role" | "send_email" | "tag_member";

export interface Workspace {
  id: string;
  clerk_user_id: string;
  name: string;
  slug: string;
  plan: Plan;
  onboarding_done: boolean;
  created_at: string;
}

export interface Member {
  id: string;
  workspace_id: string;
  email: string;
  name: string | null;
  billing_customer_id: string | null;
  billing_provider: BillingProvider | null;
  community_user_id: string | null;
  community_platform: CommunityPlatform | null;
  access_status: AccessStatus;
  created_at: string;
  subscriptions?: Subscription[];
}

export interface Subscription {
  id: string;
  workspace_id: string;
  member_id: string | null;
  billing_provider: BillingProvider;
  provider_sub_id: string;
  status: SubStatus;
  amount: number | null;
  currency: string;
  billing_interval: "month" | "year" | "week" | null;
  current_period_end: string | null;
  failed_payment_count: number;
  created_at: string;
}

export interface WebhookEvent {
  id: string;
  workspace_id: string;
  billing_provider: BillingProvider;
  provider_event_id: string;
  event_type: TriggerEvent | string;
  payload: Record<string, unknown>;
  status: "received" | "processing" | "processed" | "failed" | "skipped";
  error_message: string | null;
  retry_count: number;
  processed_at: string | null;
  created_at: string;
}

export interface AutomationRule {
  id: string;
  workspace_id: string;
  name: string;
  is_active: boolean;
  trigger_event: TriggerEvent;
  trigger_conditions: Record<string, unknown>;
  action_type: ActionType;
  action_config: Record<string, unknown>;
  priority: number;
  created_at: string;
}

export interface DashboardStats {
  active_members: number;
  past_due_members: number;
  cancelled_members: number;
  failed_events: number;
  revenue_at_risk: number;
}
