"use client";

import { useQuery } from "@tanstack/react-query";

async function fetchWatchlist() {
  const res = await fetch("/api/watchlist");
  if (!res.ok) {
    throw new Error("无法获取 watchlist 数据");
  }
  const payload = (await res.json()) as { data: Record<string, string>[] };
  return payload.data;
}

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: fetchWatchlist,
    refetchInterval: 60 * 1000,
  });
}
