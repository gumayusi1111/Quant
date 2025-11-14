"use client";

import { Card, Col, Row, Statistic } from "antd";
import { ReactNode } from "react";

interface FullPoolStatsProps {
  total: number;
  suspended: number;
  delisted: number;
}

const STAT_ITEMS: Array<{ title: string; key: keyof FullPoolStatsProps; color?: string }> = [
  { title: "全量池", key: "total" },
  { title: "停牌", key: "suspended", color: "#d97706" },
  { title: "退市", key: "delisted", color: "#dc2626" },
];

export function FullPoolStats(props: FullPoolStatsProps) {
  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      {STAT_ITEMS.map(({ title, key, color }) => (
        <Col xs={24} md={8} key={key}>
          <Card bordered={false}>
            <Statistic title={title} value={props[key]} valueStyle={color ? { color } : undefined} />
          </Card>
        </Col>
      ))}
    </Row>
  );
}
