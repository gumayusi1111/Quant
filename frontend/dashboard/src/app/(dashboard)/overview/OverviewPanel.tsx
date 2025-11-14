"use client";

import { Space } from "antd";
import { TaskControlPanel } from "@/components/TaskControlPanel";
import { useMarketRegime } from "./useMarketRegime";
import { MarketRegimeSummaryCard } from "./MarketRegimeSummaryCard";
import { MarketRegimeStatsCard } from "./MarketRegimeStatsCard";
import { MarketRegimeHistoryCard } from "./MarketRegimeHistoryCard";

export default function OverviewPanel() {
  const regimeState = useMarketRegime();

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <TaskControlPanel />
      <MarketRegimeSummaryCard
        data={regimeState.data}
        loading={regimeState.loading}
        error={regimeState.error}
      />
      <div className="regime-grid">
        <MarketRegimeStatsCard data={regimeState.data} loading={regimeState.loading} />
        <MarketRegimeHistoryCard data={regimeState.data} loading={regimeState.loading} />
      </div>
    </Space>
  );
}
