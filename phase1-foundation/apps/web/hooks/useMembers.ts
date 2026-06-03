"use client";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { clientFetch } from "@/lib/api-client";
import type { Member } from "@/types";

interface Params { status?: string; search?: string; page?: number }

export function useMembers(params: Params = {}) {
  const { getToken } = useAuth();
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError  ] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const q     = new URLSearchParams(params as Record<string, string>).toString();
      const data  = await clientFetch<{ data: Member[] }>(`/members${q ? `?${q}` : ""}`, token);
      setMembers(data?.data ?? []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(params)]);

  useEffect(() => { load(); }, [load]);

  return { members, loading, error, refetch: load };
}
