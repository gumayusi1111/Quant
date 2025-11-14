export type RegimeKey = "bull" | "sideways" | "bear";

export interface MarketRegimeSummary {
  regime: RegimeKey;
  regimeLabel: string;
  date: string;
  since: string;
  streakDays: number;
  summary: string;
}

export interface MarketRegimeResponse {
  current: MarketRegimeSummary;
  previous: {
    regime: RegimeKey;
    regimeLabel: string;
    end: string;
    days: number | null;
  } | null;
  distribution30d: {
    windowSize: number;
    counts: Record<RegimeKey, number>;
  };
  history: {
    window: number;
    points: Array<{
      date: string;
      regime: RegimeKey;
      color: string;
    }>;
  };
  meta: {
    updatedAt: string | null;
    totalRows: number;
  };
}
