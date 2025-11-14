"use client";

import { Card, Statistic, Typography, Space } from "antd";

interface ActivePoolMetaCardProps {
  updatedAt: string | null | undefined;
  total: number;
  avgAmount60: number | null | undefined;
  avgTradeRatio60: number | null | undefined;
  avgRange60: number | null | undefined;
}

const { Text } = Typography;

function formatAmount(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  if (value >= 1e8) {
    return `${(value / 1e8).toFixed(2)} 亿`;
  }
  if (value >= 1e4) {
    return `${(value / 1e4).toFixed(1)} 万`;
  }
  return value.toFixed(0);
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  return `${(value * 100).toFixed(1)}%`;
}

function formatRange(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  return `${(value * 100).toFixed(2)}%`;
}

function formatUpdatedAt(value: string | null | undefined) {
  if (!value) return "未知";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function ActivePoolMetaCard({
  updatedAt,
  total,
  avgAmount60,
  avgTradeRatio60,
  avgRange60,
}: ActivePoolMetaCardProps) {
  return (
    <Card style={{ marginBottom: 16 }}>
      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        <Text type="secondary">活跃池最近刷新：{formatUpdatedAt(updatedAt)}</Text>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 16 }}>
          <Statistic title="活跃标的数量" value={total} valueStyle={{ fontSize: 22 }} />
          <Statistic title="60 日均成交额（均值）" value={formatAmount(avgAmount60)} />
          <Statistic title="60 日交易日占比（均值）" value={formatPercent(avgTradeRatio60)} />
          <Statistic title="60 日日内振幅（均值）" value={formatRange(avgRange60)} />
        </div>
      </Space>
    </Card>
  );
}
