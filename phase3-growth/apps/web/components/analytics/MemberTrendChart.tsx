"use client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";

interface Snapshot {
  date: string;
  active_count: number;
  past_due_count: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-xs">
      <p className="text-zinc-400 mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }}>{p.name}: {p.value}</p>
      ))}
    </div>
  );
};

export function MemberTrendChart({ data }: { data: Snapshot[] }) {
  return (
    <div className="bg-zinc-900/60 border border-white/6 rounded-xl p-5">
      <p className="text-sm font-medium text-white mb-5">Member Trend</p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="date"
            tickFormatter={d => new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            tick={{ fill: "#52525b", fontSize: 11 }}
            axisLine={false} tickLine={false}
          />
          <YAxis tick={{ fill: "#52525b", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone" dataKey="active_count" name="Active"
            stroke="#8b5cf6" strokeWidth={2} dot={false} activeDot={{ r: 4 }}
          />
          <Line
            type="monotone" dataKey="past_due_count" name="Past Due"
            stroke="#f59e0b" strokeWidth={2} dot={false} activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
