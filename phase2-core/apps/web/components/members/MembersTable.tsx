"use client";
import { useState } from "react";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatDate } from "@/lib/utils";
import type { Member } from "@/types";

export function MembersTable({ members }: { members: Member[] }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const filtered = members.filter(m => {
    const q = search.toLowerCase();
    const matchSearch = !q || m.email.toLowerCase().includes(q) ||
                        (m.name?.toLowerCase().includes(q) ?? false);
    const matchFilter = filter === "all" || m.access_status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600 text-sm">⌕</span>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search by name or email..."
            className="w-full bg-zinc-900 border border-white/8 rounded-lg pl-9 pr-4 py-2.5 text-sm
              text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 transition" />
        </div>
        <div className="flex items-center gap-1 bg-zinc-900 border border-white/8 rounded-lg p-1">
          {["all","active","past_due","trialing","cancelled"].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-all
                ${filter === f ? "bg-zinc-700 text-white" : "text-zinc-500 hover:text-zinc-300"}`}>
              {f === "past_due" ? "Past Due" : f}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-zinc-900/60 border border-white/6 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              {["Member","Status","Plan","Since",""].map(h => (
                <th key={h} className="text-left px-5 py-3 text-xs text-zinc-600 font-medium uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/4">
            {filtered.map(m => (
              <tr key={m.id} className="hover:bg-white/2 transition-colors group">
                <td className="px-5 py-3.5">
                  <div>
                    <p className="text-sm font-medium text-zinc-200">{m.name ?? "—"}</p>
                    <p className="text-xs text-zinc-600">{m.email}</p>
                  </div>
                </td>
                <td className="px-5 py-3.5"><StatusBadge status={m.access_status} /></td>
                <td className="px-5 py-3.5 text-xs text-zinc-400">
                  {m.billing_provider ?? "—"}
                </td>
                <td className="px-5 py-3.5 text-xs text-zinc-500">{formatDate(m.created_at)}</td>
                <td className="px-5 py-3.5">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                    <button className="text-xs text-violet-400 hover:text-violet-300 font-medium">Sync</button>
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-12 text-center text-sm text-zinc-600">No members found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
