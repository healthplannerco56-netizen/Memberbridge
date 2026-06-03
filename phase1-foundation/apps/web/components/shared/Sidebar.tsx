"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard",             label: "Dashboard",   icon: "⬡" },
  { href: "/dashboard/members",     label: "Members",     icon: "◎" },
  { href: "/dashboard/automations", label: "Automations", icon: "⚡" },
  { href: "/dashboard/events",      label: "Event Log",   icon: "◈" },
  { href: "/dashboard/settings",    label: "Settings",    icon: "◇" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 flex-shrink-0 flex flex-col border-r border-white/5 bg-zinc-950">
      <div className="px-5 py-5 border-b border-white/5">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center text-white font-bold text-sm">M</div>
          <span className="font-semibold text-white text-sm">MemberBridge</span>
        </div>
      </div>
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV.map(item => (
          <Link key={item.href} href={item.href}
            className={cn(
              "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all",
              pathname === item.href
                ? "bg-white/8 text-white font-medium"
                : "text-zinc-500 hover:text-zinc-300 hover:bg-white/4"
            )}>
            <span className="text-base w-4 text-center opacity-80">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
