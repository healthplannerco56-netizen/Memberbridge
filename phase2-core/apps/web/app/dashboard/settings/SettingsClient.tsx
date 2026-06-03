"use client";

export function SettingsClient({ billing, community }: {
  billing: any[]; community: any[];
}) {
  const ls = billing.find(b => b.provider === "lemon_squeezy");
  const pd = billing.find(b => b.provider === "paddle");
  const ci = community.find(c => c.platform === "circle");

  return (
    <div className="px-8 py-7 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-semibold text-white tracking-tight">Settings</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Manage your integrations</p>
      </div>

      {/* Billing */}
      <div className="bg-zinc-900/60 border border-white/6 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-white/5">
          <h2 className="text-sm font-semibold text-white">Billing Provider</h2>
        </div>
        <div className="p-5 divide-y divide-white/5">
          {[
            { key:"lemon_squeezy", label:"Lemon Squeezy", data: ls },
            { key:"paddle", label:"Paddle", data: pd },
          ].map(({ key, label, data }) => (
            <div key={key} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
              <div>
                <p className={`text-sm font-medium ${data ? "text-zinc-200" : "text-zinc-500"}`}>{label}</p>
                <p className="text-xs text-zinc-600">{data ? "Connected" : "Not connected"}</p>
              </div>
              {data ? (
                <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full">Active</span>
              ) : (
                <button className="text-xs text-violet-400 hover:text-violet-300 px-3 py-1.5 bg-violet-500/10 rounded-lg font-medium">Connect</button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Community */}
      <div className="bg-zinc-900/60 border border-white/6 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-white/5">
          <h2 className="text-sm font-semibold text-white">Community Platform</h2>
        </div>
        <div className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${ci ? "text-zinc-200" : "text-zinc-500"}`}>Circle</p>
              <p className="text-xs text-zinc-600">
                {ci ? `Connected — ${ci.community_name ?? ci.community_id}` : "Not connected"}
              </p>
            </div>
            {ci ? (
              <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full">Active</span>
            ) : (
              <button className="text-xs text-violet-400 hover:text-violet-300 px-3 py-1.5 bg-violet-500/10 rounded-lg font-medium">Connect</button>
            )}
          </div>
          {ci && (
            <div className="mt-4 p-3 bg-zinc-950 rounded-lg">
              <p className="text-xs text-zinc-500 mb-1">Webhook URL</p>
              <code className="text-xs font-mono text-violet-300 break-all">
                https://api.memberbridge.io/api/v1/webhooks/lemon-squeezy/{"{your-token}"}
              </code>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
