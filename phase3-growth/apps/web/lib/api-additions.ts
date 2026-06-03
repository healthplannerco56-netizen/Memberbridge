/**
 * Phase 3 API client additions.
 * Add these methods to the `api` object in apps/web/lib/api.ts
 */

// ── Dunning ───────────────────────────────────────────────────────
// getDunningSequences:  () => apiFetch("/dunning/sequences"),
// createDunningSequence:(name: string) =>
//   apiFetch("/dunning/sequences", { method:"POST", body: JSON.stringify({ name }) }),
// getDunningLog:        (page = 1) => apiFetch(`/dunning/log?page=${page}`),

// ── Analytics ─────────────────────────────────────────────────────
// getMrrSummary:     () => apiFetch("/analytics/mrr-summary"),
// getAnalyticsTrend: (days = 30) => apiFetch(`/analytics/trend?days=${days}`),
// triggerSnapshot:   () => apiFetch("/analytics/snapshot", { method:"POST" }),
