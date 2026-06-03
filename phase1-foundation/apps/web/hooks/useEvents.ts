"use client";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { clientFetch } from "@/lib/api-client";
import type { WebhookEvent } from "@/types";

interface Params { status?: string; provider?: string; page?: number }

export function useEvents(params: Params = {}) {
  const { getToken } = useAuth();
  const [events,  setEvents ] = useState<WebhookEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError  ] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const q     = new URLSearchParams(params as Record<string, string>).toString();
      const data  = await clientFetch<{ data: WebhookEvent[] }>(`/events${q ? `?${q}` : ""}`, token);
      setEvents(data?.data ?? []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(params)]);

  useEffect(() => { load(); }, [load]);

  // Live poll every 15 seconds
  useEffect(() => {
    const id = setInterval(load, 15_000);
    return () => clearInterval(id);
  }, [load]);

  return { events, loading, error, refetch: load };
}
