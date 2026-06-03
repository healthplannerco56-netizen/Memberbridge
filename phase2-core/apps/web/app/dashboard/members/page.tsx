import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { MembersTable } from "@/components/members/MembersTable";
import type { Member } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default async function MembersPage({
  searchParams,
}: {
  searchParams: { status?: string; search?: string; page?: string };
}) {
  const { getToken, userId } = auth();
  if (!userId) redirect("/sign-in");
  const token = await getToken();

  const q = new URLSearchParams({
    ...(searchParams.status ? { status: searchParams.status } : {}),
    ...(searchParams.search ? { search: searchParams.search } : {}),
    page: searchParams.page ?? "1",
  }).toString();

  let members: Member[] = [];
  try {
    const res = await fetch(`${API_URL}/api/v1/members?${q}`, {
      headers: { Authorization: `Bearer ${token}` },
      next:    { revalidate: 0 },
    });
    if (res.ok) {
      const data = await res.json();
      members = data.data ?? [];
    }
  } catch { /* show empty state */ }

  return (
    <div className="px-8 py-7 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">Members</h1>
          <p className="text-sm text-zinc-500 mt-0.5">{members.length} members shown</p>
        </div>
      </div>
      <MembersTable members={members} />
    </div>
  );
}
