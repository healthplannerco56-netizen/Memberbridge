"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { clientFetch } from "@/lib/api-client";

const STEPS = ["Billing Provider", "Community Platform", "Automations"];

export default function OnboardingPage() {
  const [step, setStep]   = useState(0);
  const [loading, setLoading] = useState(false);
  const { getToken } = useAuth();
  const router = useRouter();

  const getAuthToken = async () => {
    const t = await getToken();
    if (!t) throw new Error("Not authenticated");
    return t;
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      const token = await getAuthToken();
      await clientFetch("/workspace/onboarding-complete", token, { method: "POST" });
      router.push("/dashboard");
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="w-full max-w-lg">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-700 mb-3">
            <span className="text-white font-bold text-lg">M</span>
          </div>
          <h1 className="text-lg font-semibold text-white">Set up MemberBridge</h1>
          <p className="text-sm text-zinc-500 mt-1">Takes about 2 minutes</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center mb-8">
          {STEPS.map((label, i) => (
            <div key={i} className="flex items-center flex-1 last:flex-none">
              <div className="flex items-center gap-2">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0
                  ${i < step  ? "bg-violet-600 text-white" :
                    i === step ? "bg-violet-600 text-white ring-4 ring-violet-600/20" :
                                 "bg-zinc-800 text-zinc-500"}`}>
                  {i < step ? "✓" : i + 1}
                </div>
                <span className={`text-xs hidden sm:block ${i === step ? "text-white font-medium" : "text-zinc-600"}`}>
                  {label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`flex-1 h-px mx-3 ${i < step ? "bg-violet-600" : "bg-zinc-800"}`} />
              )}
            </div>
          ))}
        </div>

        {/* Step content */}
        <div className="bg-zinc-900 border border-white/8 rounded-2xl p-8">
          {step === 0 && (
            <BillingStep
              getToken={getAuthToken}
              onNext={() => setStep(1)}
            />
          )}
          {step === 1 && (
            <CommunityStep
              getToken={getAuthToken}
              onNext={() => setStep(2)}
            />
          )}
          {step === 2 && (
            <AutomationStep
              onFinish={handleFinish}
              loading={loading}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// ── Step 1: Billing ───────────────────────────────────────────────

function BillingStep({
  getToken,
  onNext,
}: {
  getToken: () => Promise<string>;
  onNext: () => void;
}) {
  const [provider, setProvider] = useState("lemon_squeezy");
  const [apiKey,   setApiKey  ] = useState("");
  const [secret,   setSecret  ] = useState("");
  const [loading,  setLoading ] = useState(false);
  const [error,    setError   ] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!apiKey.trim())    return setError("API key is required");
    if (!secret.trim())    return setError("Webhook secret is required");
    setError(null);
    setLoading(true);
    try {
      const token = await getToken();
      await clientFetch(
        "/integrations/billing",
        token,
        { method: "POST", body: JSON.stringify({ provider, api_key: apiKey, webhook_secret: secret }) }
      );
      onNext();
    } catch (e: any) {
      setError(e.message || "Connection failed. Check your API key.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-white">Connect billing provider</h2>
        <p className="text-sm text-zinc-500 mt-1">Where do you collect payments?</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {[
          { value: "lemon_squeezy", label: "Lemon Squeezy" },
          { value: "paddle",        label: "Paddle" },
        ].map(opt => (
          <button
            key={opt.value}
            onClick={() => { setProvider(opt.value); setError(null); }}
            className={`p-4 rounded-xl border text-sm font-medium transition-all text-left
              ${provider === opt.value
                ? "border-violet-500 bg-violet-500/10 text-white"
                : "border-white/8 bg-zinc-800/50 text-zinc-400 hover:border-white/20"}`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <FormInput
        label="API Key"
        value={apiKey}
        onChange={v => { setApiKey(v); setError(null); }}
        placeholder={provider === "lemon_squeezy" ? "ls_live_..." : "live_..."}
        type="password"
      />
      <FormInput
        label="Webhook Secret"
        value={secret}
        onChange={v => { setSecret(v); setError(null); }}
        placeholder="whsec_..."
        type="password"
      />

      {error && <ErrorBox message={error} />}

      <div className="pt-1 space-y-2">
        <ActionButton onClick={handleSubmit} loading={loading}>
          Continue →
        </ActionButton>
        <p className="text-xs text-zinc-600 text-center">
          Your API key is encrypted before storage
        </p>
      </div>
    </div>
  );
}

// ── Step 2: Community ─────────────────────────────────────────────

function CommunityStep({
  getToken,
  onNext,
}: {
  getToken: () => Promise<string>;
  onNext: () => void;
}) {
  const [apiKey,      setApiKey     ] = useState("");
  const [communityId, setCommunityId] = useState("");
  const [loading,     setLoading    ] = useState(false);
  const [error,       setError      ] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!apiKey.trim())      return setError("API key is required");
    if (!communityId.trim()) return setError("Community ID is required");
    setError(null);
    setLoading(true);
    try {
      const token = await getToken();
      await clientFetch(
        "/integrations/community",
        token,
        { method: "POST", body: JSON.stringify({ platform: "circle", api_key: apiKey, community_id: communityId }) }
      );
      onNext();
    } catch (e: any) {
      setError(e.message || "Could not connect to Circle. Check your API key and community ID.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-white">Connect Circle</h2>
        <p className="text-sm text-zinc-500 mt-1">
          Find your API key in Circle → Settings → API.
        </p>
      </div>

      <FormInput
        label="Circle API Key"
        value={apiKey}
        onChange={v => { setApiKey(v); setError(null); }}
        placeholder="Token ..."
        type="password"
      />
      <FormInput
        label="Community ID"
        value={communityId}
        onChange={v => { setCommunityId(v); setError(null); }}
        placeholder="12345"
        hint="Found in your Circle community URL"
      />

      {error && <ErrorBox message={error} />}

      <ActionButton onClick={handleSubmit} loading={loading}>
        Connect Circle →
      </ActionButton>
    </div>
  );
}

// ── Step 3: Automations ───────────────────────────────────────────

function AutomationStep({
  onFinish,
  loading,
}: {
  onFinish: () => void;
  loading: boolean;
}) {
  const rules = [
    { trigger: "Payment successful",    action: "Grant community access" },
    { trigger: "Subscription created",  action: "Grant community access" },
    { trigger: "Subscription cancelled",action: "Revoke community access" },
    { trigger: "Trial ended",           action: "Downgrade member role"   },
  ];

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-white">Default automations ready</h2>
        <p className="text-sm text-zinc-500 mt-1">
          These 4 rules are pre-configured and active. You can edit them anytime.
        </p>
      </div>

      <div className="space-y-2">
        {rules.map((r, i) => (
          <div key={i} className="flex items-center gap-3 p-3.5 bg-zinc-800/60 rounded-xl border border-white/5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="text-xs text-zinc-500">When </span>
              <span className="text-xs font-medium text-zinc-300">{r.trigger}</span>
              <span className="text-xs text-zinc-500"> → </span>
              <span className="text-xs font-medium text-violet-400">{r.action}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="pt-1">
        <ActionButton onClick={onFinish} loading={loading}>
          🚀 Launch MemberBridge
        </ActionButton>
      </div>
    </div>
  );
}

// ── Reusable sub-components ───────────────────────────────────────

function FormInput({
  label, value, onChange, placeholder, type = "text", hint,
}: {
  label: string; value: string;
  onChange: (v: string) => void;
  placeholder?: string; type?: string; hint?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-zinc-400 font-medium mb-1.5">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-zinc-800 border border-white/8 rounded-lg px-3 py-2.5 text-sm
          text-zinc-200 placeholder:text-zinc-600 focus:outline-none
          focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition"
      />
      {hint && <p className="text-xs text-zinc-600 mt-1">{hint}</p>}
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2.5 px-3.5 py-3 bg-red-500/10 border border-red-500/20 rounded-lg">
      <span className="text-red-400 text-sm flex-shrink-0 mt-0.5">⚠</span>
      <p className="text-sm text-red-300">{message}</p>
    </div>
  );
}

function ActionButton({
  onClick, loading, children,
}: {
  onClick: () => void; loading?: boolean; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="w-full py-2.5 bg-violet-600 hover:bg-violet-500
        disabled:opacity-50 disabled:cursor-not-allowed
        rounded-lg text-sm font-semibold text-white transition-colors"
    >
      {loading ? (
        <span className="flex items-center justify-center gap-2">
          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          Please wait…
        </span>
      ) : children}
    </button>
  );
}
