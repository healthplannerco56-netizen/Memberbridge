"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { clientFetch } from "@/lib/api-client";
import type { Workspace } from "@/types";

export function useWorkspace() {
  const { getToken } = useAuth();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [loading,   setLoading  ] = useState(true);
  const [error,     setError    ] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        const data  = await clientFetch<Workspace>("/workspace", token);
        setWorkspace(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return { workspace, loading, error };
}
