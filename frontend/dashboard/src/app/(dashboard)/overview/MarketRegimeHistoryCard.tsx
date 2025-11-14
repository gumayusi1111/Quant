"use client";

import { Card, Skeleton, Typography } from "antd";
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

const REGIME_LEVEL: Record<RegimeKey, number> = {
  bull: 20,
  sideways: 60,
  bear: 100,
};

const Y_LABEL = [
  { label: "牛市", value: REGIME_LEVEL.bull },
  { label: "震荡", value: REGIME_LEVEL.sideways },
  { label: "熊市", value: REGIME_LEVEL.bear },
];

interface HistoryGroup {
  regime: RegimeKey;
  color: string;
  widthPct: number;
}

function buildGroups(points: MarketRegimeResponse["history"]["points"]): HistoryGroup[] {
  if (!points.length) return [];
  const total = points.length;
  const groups: HistoryGroup[] = [];
  let count = 0;
  let current: HistoryGroup | null = null;
  points.forEach((point) => {
    if (!current || current.regime !== point.regime) {
      if (current) {
        current.widthPct = (count / total) * 100;
        groups.push(current);
      }
      count = 1;
      current = {
        regime: point.regime,
        color: point.color,
        widthPct: 0,
      };
    } else {
      count += 1;
    }
  });
  if (current) {
    current.widthPct = (count / total) * 100;
    groups.push(current);
  }
  return groups;
}

function buildPath(points: MarketRegimeResponse["history"]["points"]) {
  if (!points.length) {
    return { path: "", width: 0 };
  }
  const width = Math.max(points.length * 12, 360);
  const height = 120;
  const step = points.length > 1 ? width / (points.length - 1) : width;
  const coords = points
    .map((point, index) => {
      const x = Math.min(step * index, width);
      const y = REGIME_LEVEL[point.regime];
      return `${x},${y}`;
    })
    .join(" ");
  return { path: coords, width, height };
}

export function MarketRegimeHistoryCard({ data, loading }: Props) {
  if (loading) {
    return (
      <Card title="近 60 日时间线">
        <Skeleton active paragraph={{ rows: 2 }} />
      </Card>
    );
  }
  if (!data || data.history.points.length === 0) {
    return (
      <Card title="近 60 日时间线">
        <Text type="secondary">暂无历史数据。</Text>
      </Card>
    );
  }

  const first = data.history.points[0];
  const last = data.history.points[data.history.points.length - 1];
  const groups = buildGroups(data.history.points);
  const { path, width, height } = buildPath(data.history.points);

  return (
    <Card title="近 60 日时间线">
      <div className="regime-history-chart">
        <div className="regime-history-chart__header">
          <Text type="secondary">起点：{first.date}</Text>
          <Text type="secondary">终点：{last.date}</Text>
        </div>
        <div className="regime-history-chart__body">
          <div className="regime-history-chart__axis">
            {Y_LABEL.map((tick) => (
              <div key={tick.label} className="regime-history-chart__tick">
                <span>{tick.label}</span>
              </div>
            ))}
          </div>
          <div className="regime-history-chart__canvas">
            <svg
              viewBox={`0 0 ${width} ${height}`}
              className="regime-history-chart__svg"
              preserveAspectRatio="none"
            >
              {groups.map((group, index) => {
                const previousWidth = groups
                  .slice(0, index)
                  .reduce((sum, item) => sum + item.widthPct, 0);
                return (
                  <rect
                    key={`${group.regime}-${index}`}
                    x={`${previousWidth}%`}
                    y="0"
                    width={`${group.widthPct}%`}
                    height="120"
                    fill={group.color}
                    opacity={0.12}
                  />
                );
              })}
              <polyline
                fill="none"
                stroke="#111827"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={path}
              />
              {data.history.points.map((point, index) => {
                const x = data.history.points.length > 1
                  ? (width / (data.history.points.length - 1)) * index
                  : width / 2;
                return (
                  <circle
                    key={`${point.date}-${index}`}
                    cx={x}
                    cy={REGIME_LEVEL[point.regime]}
                    r="3"
                    fill={point.color}
                    stroke="#fff"
                    strokeWidth="1"
                  />
                );
              })}
            </svg>
          </div>
        </div>
        <div className="regime-history-chart__legend">
          {Y_LABEL.map((tick) => (
            <div key={tick.label} className="regime-history-chart__legend-item">
              <span className="regime-history-chart__legend-dot" />
              <Text type="secondary">{tick.label}</Text>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
