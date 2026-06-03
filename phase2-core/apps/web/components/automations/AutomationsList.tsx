"use client";
import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { clientFetch } from "@/lib/api-client";
import type { AutomationRule } from "@/types";

const TRIGGER_LABELS: Record<string, string> = {
  "subscription.active":    "Payment Successful",
  "subscription.created":   "Subscription Created",
  "subscription.cancelled": "Subscription Cancelled",
  "payment.failed":         "Payment Failed",
  "trial.ended":            "Trial Ended",
  "subscription.paused":    "Subscription Paused",
  "subscription.resumed":   "Subscription Resumed",
  "subscription.expired":   "Subscription Expired",
};

const ACTION_LABELS: Record<string, string> = {
  "grant_access":  "Grant Community Access",
  "revoke_access": "Revoke Community Access",
  "change_role":   "Change Member Role",
  "send_email":    "Send Email",
  "tag_member":    "Tag Member",
};

export function AutomationsList({ initialRules }: { initialRules: AutomationRule[] }) {
  const { getToken } = useAuth();
  const [rules,   setRules  ] = useState(initialRules);
  const [toggling, setToggling] = useState<string | null>(null);
  const [error,   setError  ] = useState<string | null>(null);

  const toggle = async (rule: AutomationRule) => {
    setToggling(rule.id);
    setError(null);
    // Optimistic update
    setRules(r => r.map(x => x.id === rule.id ? { ...x, is_active: !x.is_active } : x));
    try {
      const token = await getToken();
      await clientFetch(
        `/automations/${rule.id}`,
        token,
        { method: "PATCH", body: JSON.stringify({ is_active: !rule.is_active }) }
      );
    } catch (e: any) {
      // Revert on failure
      setRules(r => r.map(x => x.id === rule.id ? { ...x, is_active: rule.is_active } : x));
      setError(e.message || "Failed to update rule");
    } finally {
      setToggling(null);
    }
  };

  return (
    <div className="space-y-3">
      {error && (
        <div className="flex items-center gap-2.5 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg">
          <span className="text-red-400 text-sm">⚠</span>
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {rules.map(rule => (
        <div
          key={rule.id}
          className="bg-zinc-900/60 border border-white/6 rounded-xl p-5 flex items-center gap-4"
        >
          {/* Toggle */}
          <button
            onClick={() => toggle(rule)}
            disabled={toggling === rule.id}
            aria-label={rule.is_active ? "Disable rule" : "Enable rule"}
            className={`relative flex-shrink-0 rounded-full transition-colors disabled:opacity-60
              ${rule.is_active ? "bg-violet-600" : "bg-zinc-700"}`}
            style={{ width: 40, height: 22 }}
          >
            <div
              className={`absolute top-1 w-3.5 h-3.5 rounded-full bg-white shadow transition-all
                ${rule.is_active ? "left-[calc(100%-18px)]" : "left-1"}`}
            />
          </button>

          {/* Details */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-zinc-200 truncate">{rule.name}</p>
            <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
              <span className="text-xs text-zinc-600">When</span>
              <span className="text-xs bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded font-mono">
                {TRIGGER_LABELS[rule.trigger_event] ?? rule.trigger_event}
              </span>
              <span className="text-xs text-zinc-600">→</span>
              <span className="text-xs bg-violet-500/15 text-violet-300 px-2 py-0.5 rounded font-mono">
                {ACTION_LABELS[rule.action_type] ?? rule.action_type}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <button
              className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-600 hover:text-zinc-300 transition-colors"
              title="Edit rule"
            >
              ✏
            </button>
            <button
              className="p-1.5 rounded-lg hover:bg-red-500/10 text-zinc-600 hover:text-red-400 transition-colors"
              title="Delete rule"
            >
              ✕
            </button>
          </div>
        </div>
      ))}

      {rules.length === 0 && (
        <div className="text-center py-12 text-sm text-zinc-600">
          No automation rules yet. Create your first rule above.
        </div>
      )}
    </div>
  );
}
