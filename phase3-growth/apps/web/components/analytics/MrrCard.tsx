import { formatCurrency } from "@/lib/utils";

export function MrrCard({
  mrr, arr, activeSubs,
}: {
  mrr: number; arr: number; activeSubs: number;
}) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {[
        { label: "Monthly Recurring Revenue", value: formatCurrency(mrr), color: "text-violet-400" },
        { label: "Annual Recurring Revenue",  value: formatCurrency(arr), color: "text-white" },
        { label: "Active Subscriptions",      value: activeSubs,          color: "text-white" },
      ].map(c => (
        <div key={c.label} className="bg-zinc-900/60 border border-white/6 rounded-xl p-5">
          <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider mb-3">{c.label}</p>
          <p className={`text-3xl font-semibold tracking-tight ${c.color}`}>{c.value}</p>
        </div>
      ))}
    </div>
  );
}
