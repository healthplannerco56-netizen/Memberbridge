import type { DashboardStats } from "@/types";
import { formatCurrency } from "@/lib/utils";

function Card({ label, value, sub, color }: {
  label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="bg-zinc-900/60 border border-white/6 rounded-xl p-5 flex flex-col gap-3">
      <span className="text-xs text-zinc-500 font-medium uppercase tracking-wider">{label}</span>
      <span className={`text-3xl font-semibold tracking-tight ${color ?? "text-white"}`}>{value}</span>
      {sub && <p className="text-xs text-zinc-600">{sub}</p>}
    </div>
  );
}

export function StatsCards({ stats }: { stats: DashboardStats }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      <Card label="Active Members"   value={stats.active_members}   sub="in community" />
      <Card label="Failed Payments"  value={stats.failed_events}    color="text-amber-400" />
      <Card label="Cancellations"    value={stats.cancelled_members} color="text-red-400" />
      <Card label="Revenue at Risk"  value={formatCurrency(stats.revenue_at_risk)}
            sub="from past-due members" color="text-orange-400" />
    </div>
  );
}
