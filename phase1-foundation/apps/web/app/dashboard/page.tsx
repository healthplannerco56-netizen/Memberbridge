import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { EventFeed } from "@/components/dashboard/EventFeed";
import type { DashboardStats, WebhookEvent } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchWithAuth<T>(path: string, token: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      next:    { revalidate: 30 },           // cache 30s
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

const EMPTY_STATS: DashboardStats = {
  active_members:   0,
  past_due_members: 0,
  cancelled_members:0,
  failed_events:    0,
  revenue_at_risk:  0,
};

export default async function DashboardPage() {
  const { getToken, userId } = auth();
  if (!userId) redirect("/sign-in");

  const token = await getToken();
  if (!token) redirect("/sign-in");

  const [stats, events] = await Promise.all([
    fetchWithAuth<DashboardStats>("/dashboard/stats",        token),
    fetchWithAuth<WebhookEvent[]>("/dashboard/recent-events", token),
  ]);

  return (
    <div className="px-8 py-7 space-y-7">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">Dashboard</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Your community billing overview</p>
        </div>
      </div>

      {/* Stats — show zeros if API unavailable */}
      <StatsCards stats={stats ?? EMPTY_STATS} />

      {/* Events — show empty state if none */}
      <EventFeed events={events ?? []} />
    </div>
  );
}
