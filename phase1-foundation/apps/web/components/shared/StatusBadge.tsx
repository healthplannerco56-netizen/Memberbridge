import type { AccessStatus } from "@/types";

const CFG: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  active:   { label:"Active",   bg:"bg-emerald-500/15", text:"text-emerald-400", dot:"bg-emerald-400" },
  past_due: { label:"Past Due", bg:"bg-amber-500/15",   text:"text-amber-400",   dot:"bg-amber-400"   },
  cancelled:{ label:"Cancelled",bg:"bg-red-500/15",     text:"text-red-400",     dot:"bg-red-400"     },
  trialing: { label:"Trial",    bg:"bg-blue-500/15",    text:"text-blue-400",    dot:"bg-blue-400"    },
  inactive: { label:"Inactive", bg:"bg-zinc-500/15",    text:"text-zinc-400",    dot:"bg-zinc-400"    },
};

export function StatusBadge({ status }: { status: string }) {
  const cfg = CFG[status] ?? CFG.inactive;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}
