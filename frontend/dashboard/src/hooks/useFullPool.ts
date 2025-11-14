"use client";

import { useQuery } from "@tanstack/react-query";

interface FullPoolResponse {
  data: Record<string, string>[];
  meta?: {
    updatedAt: string | null;
    newWithin30d: number;
    anomalyCount: number;
  };
}

async function fetchFullPool() {
  const res = await fetch("/api/full-pool");
  if (!res.ok) {
    throw new Error("无法获取全量池数据");
  }
  const payload = (await res.json()) as FullPoolResponse;
  return payload;
}

export function useFullPool() {
  return useQuery({
    queryKey: ["full-pool"],
    queryFn: fetchFullPool,
    staleTime: 5 * 60 * 1000,
  });
}
