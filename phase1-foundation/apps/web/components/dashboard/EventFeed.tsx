import type { WebhookEvent } from "@/types";
import { timeAgo } from "@/lib/utils";
import Link from "next/link";

const EVENT_STYLE: Record<string, { label: string; color: string; icon: string }> = {
  "subscription.active":    { label:"Access Granted",        color:"text-emerald-400", icon:"✓" },
  "subscription.created":   { label:"Subscription Created",  color:"text-blue-400",    icon:"+" },
  "payment.failed":         { label:"Payment Failed",        color:"text-amber-400",   icon:"!" },
  "subscription.cancelled": { label:"Cancelled",             color:"text-red-400",     icon:"×" },
  "trial.ended":            { label:"Trial Ended",           color:"text-purple-400",  icon:"◷" },
};

export function EventFeed({ events }: { events: WebhookEvent[] }) {
  return (
    <div className="bg-zinc-900/60 border border-white/6 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
        <span className="text-sm font-medium text-white">Recent Events</span>
        <Link href="/dashboard/events" className="text-xs text-zinc-500 hover:text-zinc-300">View all →</Link>
      </div>
      <div className="divide-y divide-white/4">
        {events.map(ev => {
          const cfg = EVENT_STYLE[ev.event_type] ?? { label: ev.event_type, color:"text-zinc-400", icon:"·" };
          return (
            <div key={ev.id} className="px-5 py-3.5 flex items-center gap-3 hover:bg-white/2 transition-colors">
              <div className={`w-7 h-7 rounded-lg bg-zinc-800 flex items-center justify-center text-sm ${cfg.color} flex-shrink-0`}>
                {cfg.icon}
              </div>
              <div className="flex-1 min-w-0">
                <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
                <p className="text-xs text-zinc-600 mt-0.5">{ev.billing_provider}</p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className={`w-1.5 h-1.5 rounded-full ${ev.status === "processed" ? "bg-emerald-400" : ev.status === "failed" ? "bg-red-400" : "bg-zinc-400"}`} />
                <span className="text-xs text-zinc-600">{timeAgo(ev.created_at)}</span>
              </div>
            </div>
          );
        })}
        {events.length === 0 && (
          <p className="px-5 py-8 text-sm text-zinc-600 text-center">
            No events yet. Connect a billing provider to get started.
          </p>
        )}
      </div>
    </div>
  );
}
