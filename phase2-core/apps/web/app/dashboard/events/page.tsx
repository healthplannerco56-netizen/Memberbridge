import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { EventsTable } from "@/components/dashboard/EventsTable";
import type { WebhookEvent } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default async function EventsPage({
  searchParams,
}: {
  searchParams: { status?: string; provider?: string; page?: string };
}) {
  const { getToken, userId } = auth();
  if (!userId) redirect("/sign-in");
  const token = await getToken();

  const q = new URLSearchParams({
    ...(searchParams.status   ? { status:   searchParams.status }   : {}),
    ...(searchParams.provider ? { provider: searchParams.provider } : {}),
    page: searchParams.page ?? "1",
  }).toString();

  let events: WebhookEvent[] = [];
  try {
    const res = await fetch(`${API_URL}/api/v1/events?${q}`, {
      headers: { Authorization: `Bearer ${token}` },
      next:    { revalidate: 0 },
    });
    if (res.ok) {
      const data = await res.json();
      events = data.data ?? [];
    }
  } catch { /* show empty state */ }

  return (
    <div className="px-8 py-7 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white tracking-tight">Event Log</h1>
        <p className="text-sm text-zinc-500 mt-0.5">All incoming webhook events</p>
      </div>
      <EventsTable events={events} />
    </div>
  );
}
