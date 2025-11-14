"use client";

import { Card, Typography } from "antd";

export default function ExecutionPage() {
  return (
    <section className="page-panel">
      <Card title="执行池" bordered={false}>
        <Typography.Text style={{ color: "#111827" }}>
          功能开发中，后续将在此展示 pending orders。
        </Typography.Text>
      </Card>
    </section>
  );
}
