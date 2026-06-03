-- ================================================================
-- MemberBridge — Phase 1 Database Schema
-- Run in Supabase SQL Editor: https://app.supabase.com/project/_/sql
-- ================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── WORKSPACES ──────────────────────────────────────────────────
CREATE TABLE workspaces (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clerk_user_id   TEXT NOT NULL UNIQUE,
  name            TEXT NOT NULL,
  slug            TEXT NOT NULL UNIQUE,
  plan            TEXT NOT NULL DEFAULT 'starter'
                    CHECK (plan IN ('starter','pro','business')),
  onboarding_done BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── BILLING INTEGRATIONS ────────────────────────────────────────
CREATE TABLE billing_integrations (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id   UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  provider       TEXT NOT NULL
                   CHECK (provider IN ('paddle','lemon_squeezy','stripe','paypal')),
  is_active      BOOLEAN NOT NULL DEFAULT FALSE,
  webhook_secret TEXT,
  api_key_enc    TEXT,
  config         JSONB NOT NULL DEFAULT '{}',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (workspace_id, provider)
);

-- ── COMMUNITY INTEGRATIONS ──────────────────────────────────────
CREATE TABLE community_integrations (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id   UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  platform       TEXT NOT NULL
                   CHECK (platform IN ('circle','skool','mighty_networks')),
  is_active      BOOLEAN NOT NULL DEFAULT FALSE,
  api_key_enc    TEXT,
  community_id   TEXT,
  community_name TEXT,
  config         JSONB NOT NULL DEFAULT '{}',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (workspace_id, platform)
);

-- ── MEMBERS ─────────────────────────────────────────────────────
CREATE TABLE members (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id        UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  email               TEXT NOT NULL,
  name                TEXT,
  billing_customer_id TEXT,
  billing_provider    TEXT,
  community_user_id   TEXT,
  community_platform  TEXT,
  access_status       TEXT NOT NULL DEFAULT 'inactive'
                        CHECK (access_status IN ('active','inactive','past_due',
                                                 'cancelled','trialing')),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (workspace_id, email)
);

CREATE INDEX idx_members_workspace ON members(workspace_id);
CREATE INDEX idx_members_status    ON members(access_status);
CREATE INDEX idx_members_billing   ON members(billing_customer_id);

-- ── SUBSCRIPTIONS ───────────────────────────────────────────────
CREATE TABLE subscriptions (
  id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id         UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  member_id            UUID REFERENCES members(id) ON DELETE SET NULL,
  billing_provider     TEXT NOT NULL,
  provider_sub_id      TEXT NOT NULL,
  provider_plan_id     TEXT,
  provider_customer_id TEXT,
  status               TEXT NOT NULL DEFAULT 'active'
                         CHECK (status IN ('trialing','active','past_due',
                                          'cancelled','expired','paused')),
  trial_ends_at        TIMESTAMPTZ,
  current_period_start TIMESTAMPTZ,
  current_period_end   TIMESTAMPTZ,
  cancelled_at         TIMESTAMPTZ,
  amount               NUMERIC(10,2),
  currency             TEXT DEFAULT 'USD',
  billing_interval     TEXT CHECK (billing_interval IN ('month','year','week')),
  failed_payment_count INT NOT NULL DEFAULT 0,
  last_payment_failed_at TIMESTAMPTZ,
  dunning_step         INT NOT NULL DEFAULT 0,
  metadata             JSONB NOT NULL DEFAULT '{}',
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (billing_provider, provider_sub_id)
);

CREATE INDEX idx_subs_workspace ON subscriptions(workspace_id);
CREATE INDEX idx_subs_member    ON subscriptions(member_id);
CREATE INDEX idx_subs_status    ON subscriptions(status);

-- ── WEBHOOK EVENTS ──────────────────────────────────────────────
CREATE TABLE webhook_events (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id      UUID REFERENCES workspaces(id) ON DELETE SET NULL,
  billing_provider  TEXT NOT NULL,
  provider_event_id TEXT NOT NULL,
  event_type        TEXT NOT NULL,
  payload           JSONB NOT NULL,
  status            TEXT NOT NULL DEFAULT 'received'
                      CHECK (status IN ('received','processing','processed',
                                        'failed','skipped')),
  error_message     TEXT,
  retry_count       INT NOT NULL DEFAULT 0,
  processed_at      TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (billing_provider, provider_event_id)
);

CREATE INDEX idx_wh_workspace ON webhook_events(workspace_id);
CREATE INDEX idx_wh_status    ON webhook_events(status);
CREATE INDEX idx_wh_created   ON webhook_events(created_at DESC);

-- ── AUTOMATION RULES ────────────────────────────────────────────
CREATE TABLE automation_rules (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id       UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name               TEXT NOT NULL,
  is_active          BOOLEAN NOT NULL DEFAULT TRUE,
  trigger_event      TEXT NOT NULL
                       CHECK (trigger_event IN (
                         'subscription.created','subscription.active',
                         'payment.failed','subscription.cancelled',
                         'subscription.expired','trial.ended',
                         'subscription.paused','subscription.resumed'
                       )),
  trigger_conditions JSONB DEFAULT '{}',
  action_type        TEXT NOT NULL
                       CHECK (action_type IN (
                         'grant_access','revoke_access',
                         'change_role','send_email','tag_member'
                       )),
  action_config      JSONB NOT NULL DEFAULT '{}',
  priority           INT NOT NULL DEFAULT 100,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rules_workspace ON automation_rules(workspace_id);
CREATE INDEX idx_rules_trigger   ON automation_rules(trigger_event);

-- ── AUTOMATION EXECUTIONS ───────────────────────────────────────
CREATE TABLE automation_executions (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id     UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  rule_id          UUID REFERENCES automation_rules(id) ON DELETE SET NULL,
  webhook_event_id UUID REFERENCES webhook_events(id) ON DELETE SET NULL,
  member_id        UUID REFERENCES members(id) ON DELETE SET NULL,
  trigger_event    TEXT NOT NULL,
  action_type      TEXT NOT NULL,
  status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','success','failed','skipped')),
  result           JSONB DEFAULT '{}',
  error_message    TEXT,
  executed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exec_workspace ON automation_executions(workspace_id);
CREATE INDEX idx_exec_member    ON automation_executions(member_id);

-- ── DUNNING ─────────────────────────────────────────────────────
CREATE TABLE dunning_sequences (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name         TEXT NOT NULL DEFAULT 'Default Dunning',
  is_active    BOOLEAN NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE dunning_steps (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  dunning_sequence_id UUID NOT NULL REFERENCES dunning_sequences(id) ON DELETE CASCADE,
  step_number         INT NOT NULL,
  delay_hours         INT NOT NULL,
  email_subject       TEXT NOT NULL,
  email_body_html     TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (dunning_sequence_id, step_number)
);

CREATE TABLE dunning_email_log (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id      UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  subscription_id   UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
  dunning_step_id   UUID REFERENCES dunning_steps(id) ON DELETE SET NULL,
  step_number       INT NOT NULL,
  email             TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'queued'
                      CHECK (status IN ('queued','sent','failed','bounced')),
  resend_message_id TEXT,
  scheduled_for     TIMESTAMPTZ NOT NULL,
  sent_at           TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── AUDIT LOGS ──────────────────────────────────────────────────
CREATE TABLE audit_logs (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id  UUID REFERENCES workspaces(id) ON DELETE SET NULL,
  actor_type    TEXT NOT NULL CHECK (actor_type IN ('system','user','webhook')),
  actor_id      TEXT,
  action        TEXT NOT NULL,
  resource_type TEXT,
  resource_id   TEXT,
  metadata      JSONB DEFAULT '{}',
  ip_address    INET,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_workspace ON audit_logs(workspace_id);
CREATE INDEX idx_audit_created   ON audit_logs(created_at DESC);

-- ── ROW LEVEL SECURITY ──────────────────────────────────────────
ALTER TABLE workspaces             ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_integrations   ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE members                ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions          ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_events         ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_rules       ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_executions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE dunning_sequences      ENABLE ROW LEVEL SECURITY;
ALTER TABLE dunning_steps          ENABLE ROW LEVEL SECURITY;
ALTER TABLE dunning_email_log      ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs             ENABLE ROW LEVEL SECURITY;

-- ── UPDATED_AT TRIGGER ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_workspaces_upd BEFORE UPDATE ON workspaces
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_billing_upd BEFORE UPDATE ON billing_integrations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_community_upd BEFORE UPDATE ON community_integrations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_members_upd BEFORE UPDATE ON members
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_subs_upd BEFORE UPDATE ON subscriptions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_rules_upd BEFORE UPDATE ON automation_rules
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
