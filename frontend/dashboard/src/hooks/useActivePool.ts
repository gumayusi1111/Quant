"use client";

import { useQuery } from "@tanstack/react-query";

interface ActivePoolResponse {
  data: Record<string, string>[];
  meta?: {
    updatedAt: string | null;
    total: number;
    avgAmount60: number | null;
    avgTradeRatio60: number | null;
    avgRange60: number | null;
  };
}

async function fetchActivePool() {
  const res = await fetch("/api/active-pool");
  if (!res.ok) {
    throw new Error("无法获取活跃池数据");
  }
  const payload = (await res.json()) as ActivePoolResponse;
  return payload;
}

export function useActivePool() {
  return useQuery({
    queryKey: ["active-pool"],
    queryFn: fetchActivePool,
    staleTime: 5 * 60 * 1000,
  });
}
