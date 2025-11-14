"use client";

import { Card, Space, Tag, Typography, Skeleton, Alert } from "antd";
import type { MarketRegimeResponse } from "./market-regime-types";

const { Text } = Typography;

interface Props {
  data: MarketRegimeResponse | null;
  loading: boolean;
  error: string | null;
}

const REGIME_COLORS: Record<string, string> = {
  bull: "#15803d",
  sideways: "#2563eb",
  bear: "#b91c1c",
};

function formatDateTime(value: string | null | undefined) {
  if (!value) return "未知";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, "0")}/${String(
    date.getDate(),
  ).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(
    date.getMinutes(),
  ).padStart(2, "0")}:${String(date.getSeconds()).padStart(2, "0")}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "未知";
  if (value.includes("/")) return value;
  if (value.includes("-")) {
    const parts = value.split("-");
    if (parts.length === 3) {
      return `${parts[0]}/${parts[1]}/${parts[2]}`;
    }
  }
  return value;
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="regime-summary__stat">
      <Text type="secondary">{label}</Text>
      <Text strong>{value}</Text>
    </div>
  );
}

export function MarketRegimeSummaryCard({ data, loading, error }: Props) {
  if (loading) {
    return (
      <Card title="今日市场环境">
        <Skeleton active paragraph={{ rows: 2 }} />
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card title="今日市场环境">
        <Alert
          type="warning"
          message={error ?? "暂无市场环境记录，请先执行市场环境检测任务。"}
          showIcon
        />
      </Card>
    );
  }

  const badgeColor = REGIME_COLORS[data.current.regime] ?? "#111827";

  return (
    <Card title="今日市场环境">
      <div className="regime-summary">
        <div className="regime-summary__badge">
          <Tag color={badgeColor} style={{ color: "#fff", fontWeight: 600, fontSize: 14 }}>
            {data.current.regimeLabel}
          </Tag>
          <Text className="regime-summary__note">策略：{data.current.summary}</Text>
        </div>
        <div className="regime-summary__stats">
          <SummaryStat label="判定日" value={formatDate(data.current.date)} />
          <SummaryStat label="生效日" value={formatDate(data.current.since)} />
          <SummaryStat label="连续天数" value={`${data.current.streakDays} 天`} />
          <SummaryStat
            label="记录总量"
            value={`${data.meta.totalRows} 天`}
          />
        </div>
        <div className="regime-summary__status">
          <Text strong>
            连续 {data.current.streakDays} 天保持 {data.current.regimeLabel}
          </Text>
          {data.previous ? (
            <Text type="secondary">
              上一次切换：{data.previous.regimeLabel} · 结束于 {formatDate(data.previous.end)} ·
              持续 {data.previous.days ?? "?"} 天
            </Text>
          ) : (
            <Text type="secondary">暂无历史切换记录。</Text>
          )}
          <Text type="secondary">
            数据更新时间：{formatDateTime(data.meta.updatedAt)}
          </Text>
        </div>
      </div>
    </Card>
  );
}
