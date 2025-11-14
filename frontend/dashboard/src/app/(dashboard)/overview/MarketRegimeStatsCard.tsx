"use client";

import { Card, Space, Typography, Skeleton } from "antd";
import type { MarketRegimeResponse, RegimeKey } from "./market-regime-types";

const { Text } = Typography;

interface Props {
  data: MarketRegimeResponse | null;
  loading: boolean;
}

const LABEL_MAP: Record<RegimeKey, string> = {
  bull: "牛市",
  sideways: "震荡",
  bear: "熊市",
};

const COLOR_MAP: Record<RegimeKey, string> = {
  bull: "#16a34a",
  sideways: "#0ea5e9",
  bear: "#dc2626",
};

export function MarketRegimeStatsCard({ data, loading }: Props) {
  if (loading) {
    return (
      <Card title="最近 30 日占比">
        <Skeleton active paragraph={{ rows: 3 }} />
      </Card>
    );
  }
  if (!data) {
    return null;
  }

  const total = Math.max(1, data.distribution30d.windowSize);

  return (
    <Card title="最近 30 日占比">
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        {Object.entries(data.distribution30d.counts).map(([key, value]) => {
          const regime = key as RegimeKey;
          const pct = Math.round((value / total) * 100);
          return (
            <div key={regime} className="regime-progress">
              <div className="regime-progress__header">
                <Text strong>{LABEL_MAP[regime]}</Text>
                <Text type="secondary">
                  {value} 天 · {pct}%
                </Text>
              </div>
              <div className="regime-progress__bar">
                <div
                  className="regime-progress__fill"
                  style={{ width: `${pct}%`, backgroundColor: COLOR_MAP[regime] }}
                />
              </div>
            </div>
          );
        })}
        <Text type="secondary">
          统计窗口 {data.distribution30d.windowSize} 天 · 当前连续 {data.current.streakDays} 天为{" "}
          {LABEL_MAP[data.current.regime]}。
        </Text>
      </Space>
    </Card>
  );
}
