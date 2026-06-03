-- ================================================================
-- MemberBridge — Phase 3 Analytics Schema
-- Run AFTER 001_initial_schema.sql
-- ================================================================

-- Daily snapshots for trend charts
CREATE TABLE analytics_snapshots (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  date         DATE NOT NULL,
  active_count INT NOT NULL DEFAULT 0,
  past_due_count INT NOT NULL DEFAULT 0,
  cancelled_count INT NOT NULL DEFAULT 0,
  new_members  INT NOT NULL DEFAULT 0,
  churned      INT NOT NULL DEFAULT 0,
  mrr          NUMERIC(12,2) NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (workspace_id, date)
);

CREATE INDEX idx_snapshots_workspace_date ON analytics_snapshots(workspace_id, date DESC);

ALTER TABLE analytics_snapshots ENABLE ROW LEVEL SECURITY;
