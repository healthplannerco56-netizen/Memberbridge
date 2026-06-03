import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { MrrCard } from "@/components/analytics/MrrCard";
import { MemberTrendChart } from "@/components/analytics/MemberTrendChart";
import { MrrTrendChart } from "@/components/analytics/MrrTrendChart";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAuth<T>(path: string, token: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      next:    { revalidate: 60 },
    });
    return res.ok ? (res.json() as Promise<T>) : null;
  } catch {
    return null;
  }
}

interface MrrSummary {
  mrr: number;
  arr: number;
  active_subs: number;
  monthly_subs: number;
  annual_subs: number;
}

interface Snapshot {
  date: string;
  active_count: number;
  past_due_count: number;
  mrr: number;
}

export default async function AnalyticsPage() {
  const { getToken, userId } = auth();
  if (!userId) redirect("/sign-in");
  const token = await getToken();
  if (!token) redirect("/sign-in");

  const [mrr, trend] = await Promise.all([
    fetchAuth<MrrSummary>("/analytics/mrr-summary", token),
    fetchAuth<Snapshot[]>("/analytics/trend?days=30", token),
  ]);

  const mrrData   = mrr   ?? { mrr: 0, arr: 0, active_subs: 0, monthly_subs: 0, annual_subs: 0 };
  const trendData = trend ?? [];

  return (
    <div className="px-8 py-7 space-y-7">
      <div>
        <h1 className="text-xl font-semibold text-white tracking-tight">Analytics</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Revenue and membership trends (last 30 days)</p>
      </div>

      <MrrCard
        mrr={mrrData.mrr}
        arr={mrrData.arr}
        activeSubs={mrrData.active_subs}
      />

      {trendData.length === 0 ? (
        <div className="bg-zinc-900/60 border border-white/6 rounded-xl p-12 text-center">
          <p className="text-sm text-zinc-500">
            No analytics data yet. Snapshots are taken daily after the first webhook event.
          </p>
          <p className="text-xs text-zinc-600 mt-2">
            You can trigger a manual snapshot via the API: POST /api/v1/analytics/snapshot
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-5">
          <MemberTrendChart data={trendData} />
          <MrrTrendChart    data={trendData} />
        </div>
      )}
    </div>
  );
}
