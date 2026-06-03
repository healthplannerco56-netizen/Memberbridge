import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { AutomationsList } from "@/components/automations/AutomationsList";
import type { AutomationRule } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default async function AutomationsPage() {
  const { getToken, userId } = auth();
  if (!userId) redirect("/sign-in");
  const token = await getToken();

  let rules: AutomationRule[] = [];
  try {
    const res = await fetch(`${API_URL}/api/v1/automations`, {
      headers: { Authorization: `Bearer ${token}` },
      next:    { revalidate: 0 },
    });
    if (res.ok) rules = await res.json();
  } catch { /* show empty state */ }

  return (
    <div className="px-8 py-7 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">Automations</h1>
          <p className="text-sm text-zinc-500 mt-0.5">Rules that run when billing events occur</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 rounded-lg text-sm text-white font-medium transition-colors">
          + New Rule
        </button>
      </div>
      <AutomationsList initialRules={rules} />
    </div>
  );
}
