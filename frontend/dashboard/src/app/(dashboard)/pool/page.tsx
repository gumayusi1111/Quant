"use client";

import { Card, Typography } from "antd";

export default function PoolPage() {
  return (
    <section className="page-panel">
      <Card title="观察池" bordered={false}>
        <Typography.Text style={{ color: "#111827" }}>
          功能开发中，后续将在此展示 watch_pool 数据。
        </Typography.Text>
      </Card>
    </section>
  );
}
