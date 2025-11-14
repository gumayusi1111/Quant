"use client";

import { useEffect, useState } from "react";
import type { MarketRegimeResponse } from "./market-regime-types";

interface MarketRegimeState {
  data: MarketRegimeResponse | null;
  loading: boolean;
  error: string | null;
}

export function useMarketRegime(): MarketRegimeState {
  const [state, setState] = useState<MarketRegimeState>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      setState((prev) => ({ ...prev, loading: true }));
      try {
        const response = await fetch("/api/market-regime", { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`请求失败：${response.status}`);
        }
        const payload = (await response.json()) as { data: MarketRegimeResponse | null };
        if (!cancelled) {
          setState({
            data: payload.data,
            loading: false,
            error: null,
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            data: null,
            loading: false,
            error: error instanceof Error ? error.message : "未知错误",
          });
        }
      }
    }
    fetchData();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
