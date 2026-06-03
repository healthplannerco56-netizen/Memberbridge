"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { clientFetch } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

interface DunningLogRow {
  id: string;
  email: string;
  step_number: number;
  status: "queued" | "sent" | "failed" | "bounced" | "cancelled";
  scheduled_for: string;
  sent_at: string | null;
}

const STEP_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: "Step 1 — Immediate",  color: "text-blue-400"  },
  2: { label: "Step 2 — 48 hours",   color: "text-amber-400" },
  3: { label: "Step 3 — Final (5d)", color: "text-red-400"   },
};

const STATUS_STYLE: Record<string, string> = {
  queued:    "bg-blue-500/10 text-blue-400",
  sent:      "bg-emerald-500/10 text-emerald-400",
  failed:    "bg-red-500/10 text-red-400",
  bounced:   "bg-orange-500/10 text-orange-400",
  cancelled: "bg-zinc-700 text-zinc-400",
};

export function DunningClient() {
  const { getToken } = useAuth();
  const [log,     setLog    ] = useState<DunningLogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError  ] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        const data  = await clientFetch<{ data: DunningLogRow[] }>("/dunning/log?page=1", token);
        setLog(data?.data ?? []);
      } catch (e: any) {
        setError(e.message || "Failed to load dunning log");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="px-8 py-7 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white tracking-tight">Dunning</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Automated failed-payment email sequences</p>
      </div>

      {/* Sequence overview */}
      <div className="bg-zinc-900/60 border border-white/6 rounded-xl p-5 space-y-4">
        <p className="text-sm font-semibold text-white">Default 3-step sequence</p>
        <div className="space-y-3">
          {[
            { step: 1, delay: "Immediately",  desc: "First payment failed notice, update link" },
            { step: 2, delay: "After 48h",    desc: "Reminder with urgency"                    },
            { step: 3, delay: "After 5 days", desc: "Final notice — access cancelled in 24h"   },
          ].map(s => (
            <div key={s.step} className="flex items-center gap-4">
              <div className="w-7 h-7 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-semibold text-zinc-300 flex-shrink-0">
                {s.step}
              </div>
              <div className="flex-1">
                <p className="text-sm text-zinc-300">{s.desc}</p>
              </div>
              <span className="text-xs text-zinc-500 font-mono flex-shrink-0">{s.delay}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Email log */}
      <div>
        <p className="text-sm font-semibold text-white mb-3">Email Log</p>
        <div className="bg-zinc-900/60 border border-white/6 rounded-xl overflow-hidden">
          {loading ? (
            <div className="px-5 py-10 text-center">
              <div className="inline-block w-5 h-5 border-2 border-zinc-600 border-t-violet-500 rounded-full animate-spin" />
            </div>
          ) : error ? (
            <div className="px-5 py-10 text-center text-sm text-red-400">{error}</div>
          ) : log.length === 0 ? (
            <div className="px-5 py-12 text-center">
              <p className="text-sm text-zinc-500">No dunning emails sent yet.</p>
              <p className="text-xs text-zinc-600 mt-1">They appear here automatically when a payment fails.</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  {["Email", "Step", "Status", "Scheduled", "Sent"].map(h => (
                    <th key={h} className="text-left px-5 py-3 text-xs text-zinc-600 font-medium uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/4">
                {log.map(row => {
                  const sc = STEP_LABELS[row.step_number] ?? { label: `Step ${row.step_number}`, color: "text-zinc-400" };
                  return (
                    <tr key={row.id} className="hover:bg-white/2 transition-colors">
                      <td className="px-5 py-3.5 text-sm text-zinc-300">{row.email}</td>
                      <td className="px-5 py-3.5">
                        <span className={`text-xs font-medium ${sc.color}`}>{sc.label}</span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLE[row.status] ?? "bg-zinc-700 text-zinc-400"}`}>
                          {row.status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-xs text-zinc-500">{formatDate(row.scheduled_for)}</td>
                      <td className="px-5 py-3.5 text-xs text-zinc-500">{row.sent_at ? formatDate(row.sent_at) : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
