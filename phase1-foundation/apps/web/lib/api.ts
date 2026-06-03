/**
 * Server-side API client.
 * Used in Next.js Server Components and Route Handlers.
 * Automatically injects the Clerk token from server context.
 *
 * For Client Components / hooks, use lib/api-client.ts instead.
 */
import { auth } from "@clerk/nextjs/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { getToken } = auth();
  const token = await getToken();

  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    next: { revalidate: 0 }, // no cache by default (real-time data)
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  // ── Workspace ──────────────────────────────────────────────────
  getWorkspace:       ()          => apiFetch("/workspace"),
  createWorkspace:    (name: string) =>
    apiFetch("/workspace", { method: "POST", body: JSON.stringify({ name }) }),
  completeOnboarding: ()          =>
    apiFetch("/workspace/onboarding-complete", { method: "POST" }),

  // ── Dashboard ──────────────────────────────────────────────────
  getStats:           ()          => apiFetch("/dashboard/stats"),
  getRecentEvents:    ()          => apiFetch("/dashboard/recent-events"),

  // ── Integrations ───────────────────────────────────────────────
  listBilling:        ()          => apiFetch("/integrations/billing"),
  createBilling:      (d: { provider: string; api_key: string; webhook_secret: string }) =>
    apiFetch("/integrations/billing", { method: "POST", body: JSON.stringify(d) }),
  deleteBilling:      (provider: string) =>
    apiFetch(`/integrations/billing/${provider}`, { method: "DELETE" }),

  listCommunity:      ()          => apiFetch("/integrations/community"),
  createCommunity:    (d: { platform: string; api_key: string; community_id: string }) =>
    apiFetch("/integrations/community", { method: "POST", body: JSON.stringify(d) }),
  deleteCommunity:    (platform: string) =>
    apiFetch(`/integrations/community/${platform}`, { method: "DELETE" }),

  // ── Members ────────────────────────────────────────────────────
  listMembers:        (p?: { status?: string; search?: string; page?: number }) => {
    const q = new URLSearchParams(p as Record<string, string>).toString();
    return apiFetch(`/members${q ? `?${q}` : ""}`);
  },
  getMember:          (id: string) => apiFetch(`/members/${id}`),
  syncMember:         (id: string) =>
    apiFetch(`/members/${id}/sync`, { method: "POST" }),

  // ── Automations ────────────────────────────────────────────────
  listRules:          ()          => apiFetch("/automations"),
  createRule:         (d: object) =>
    apiFetch("/automations", { method: "POST", body: JSON.stringify(d) }),
  updateRule:         (id: string, d: object) =>
    apiFetch(`/automations/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
  deleteRule:         (id: string) =>
    apiFetch(`/automations/${id}`, { method: "DELETE" }),
  listExecutions:     (page = 1)  => apiFetch(`/automations/executions?page=${page}`),

  // ── Events ─────────────────────────────────────────────────────
  listEvents:         (p?: { status?: string; provider?: string; page?: number }) => {
    const q = new URLSearchParams(p as Record<string, string>).toString();
    return apiFetch(`/events${q ? `?${q}` : ""}`);
  },
  getEvent:           (id: string) => apiFetch(`/events/${id}`),
  retryEvent:         (id: string) =>
    apiFetch(`/events/${id}/retry`, { method: "POST" }),

  // ── Dunning (Phase 3) ──────────────────────────────────────────
  getDunningSequences:  ()          => apiFetch("/dunning/sequences"),
  createDunningSequence:(name: string) =>
    apiFetch("/dunning/sequences", { method: "POST", body: JSON.stringify({ name }) }),
  getDunningLog:        (page = 1)  => apiFetch(`/dunning/log?page=${page}`),

  // ── Analytics (Phase 3) ────────────────────────────────────────
  getMrrSummary:        ()          => apiFetch("/analytics/mrr-summary"),
  getAnalyticsTrend:    (days = 30) => apiFetch(`/analytics/trend?days=${days}`),
};
