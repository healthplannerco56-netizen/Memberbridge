"use client";
import { useState } from "react";
import { timeAgo } from "@/lib/utils";
import type { WebhookEvent } from "@/types";

export function EventsTable({ events }: { events: WebhookEvent[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="bg-zinc-900/60 border border-white/6 rounded-xl overflow-hidden">
      <div className="divide-y divide-white/4">
        {events.map(ev => (
          <div key={ev.id}>
            <button onClick={() => setExpanded(expanded === ev.id ? null : ev.id)}
              className="w-full px-5 py-3.5 flex items-center gap-3 hover:bg-white/2 transition-colors text-left">
              <span className="flex-1 font-mono text-xs text-zinc-300">{ev.event_type}</span>
              <span className="text-xs text-zinc-500">{ev.billing_provider}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                ev.status === "processed" ? "bg-emerald-500/10 text-emerald-400" :
                ev.status === "failed"    ? "bg-red-500/10 text-red-400" :
                "bg-zinc-700 text-zinc-400"
              }`}>{ev.status}</span>
              <span className="text-xs text-zinc-600">{timeAgo(ev.created_at)}</span>
            </button>
            {expanded === ev.id && (
              <div className="px-5 pb-4 bg-zinc-950/40">
                <pre className="text-xs text-zinc-400 font-mono overflow-auto bg-zinc-950 border border-white/6 rounded-lg p-4">
                  {JSON.stringify(ev.payload, null, 2)}
                </pre>
                {ev.status === "failed" && (
                  <p className="mt-2 text-xs text-red-400">Error: {ev.error_message}</p>
                )}
              </div>
            )}
          </div>
        ))}
        {events.length === 0 && (
          <p className="px-5 py-12 text-sm text-zinc-600 text-center">No events yet</p>
        )}
      </div>
    </div>
  );
}
