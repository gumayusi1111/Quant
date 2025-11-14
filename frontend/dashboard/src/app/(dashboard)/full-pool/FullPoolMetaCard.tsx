"use client";

import { Card, Descriptions } from "antd";
import dayjs from "dayjs";

interface FullPoolMetaCardProps {
  updatedAt?: string | null;
  newWithin30d?: number;
  anomalyCount?: number;
}

export function FullPoolMetaCard({ updatedAt, newWithin30d = 0, anomalyCount = 0 }: FullPoolMetaCardProps) {
  const formatted = updatedAt ? dayjs(updatedAt).format("YYYY/MM/DD HH:mm:ss") : "-";
  return (
    <Card style={{ marginBottom: 16 }} bordered={false}>
      <Descriptions size="small" column={{ xs: 1, sm: 3 }}>
        <Descriptions.Item label="最近刷新">{formatted}</Descriptions.Item>
        <Descriptions.Item label="近30日新增">{newWithin30d}</Descriptions.Item>
        <Descriptions.Item label="异常记录">{anomalyCount}</Descriptions.Item>
      </Descriptions>
    </Card>
  );
}
