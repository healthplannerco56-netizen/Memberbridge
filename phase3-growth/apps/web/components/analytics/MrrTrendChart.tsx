"use client";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";

interface Snapshot { date: string; mrr: number; }

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-xs">
      <p className="text-zinc-400 mb-1">{label}</p>
      <p className="text-violet-400">MRR: ${payload[0]?.value?.toLocaleString()}</p>
    </div>
  );
};

export function MrrTrendChart({ data }: { data: Snapshot[] }) {
  return (
    <div className="bg-zinc-900/60 border border-white/6 rounded-xl p-5">
      <p className="text-sm font-medium text-white mb-5">MRR Trend</p>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
          <defs>
            <linearGradient id="mrrGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#8b5cf6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}   />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="date"
            tickFormatter={d => new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            tick={{ fill: "#52525b", fontSize: 11 }}
            axisLine={false} tickLine={false}
          />
          <YAxis
            tickFormatter={v => `$${v}`}
            tick={{ fill: "#52525b", fontSize: 11 }}
            axisLine={false} tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone" dataKey="mrr" name="MRR"
            stroke="#8b5cf6" strokeWidth={2}
            fill="url(#mrrGrad)" dot={false} activeDot={{ r: 4 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
