"use client";

import { Card, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useMemo } from "react";
import { useWatchlist } from "@/hooks/useWatchlist";

interface WatchRow {
  ts_code: string;
  tier?: string;
  env?: string;
  score?: string;
  close?: string;
  pct_chg?: string;
}

export function WatchlistSection() {
  const { data = [], isLoading, isError } = useWatchlist();

  const columns: ColumnsType<WatchRow> = useMemo(
    () => [
      { title: "代码", dataIndex: "ts_code", width: 140 },
      {
        title: "分级",
        dataIndex: "tier",
        render: (tier: string | undefined) =>
          tier ? (
            <Tag color={tier === "A" ? "gold" : tier === "B" ? "blue" : "purple"}>
              {tier}
            </Tag>
          ) : (
            "-"
          ),
      },
      { title: "环境", dataIndex: "env", render: (env: string) => env || "-" },
      { title: "得分", dataIndex: "score", render: (score) => score ?? "-" },
      {
        title: "收盘价",
        dataIndex: "close",
        render: (price: string | undefined) =>
          price ? Number(price).toFixed(3) : "-",
      },
      {
        title: "涨跌幅",
        dataIndex: "pct_chg",
        render: (pct: string | undefined) =>
          pct ? `${Number(pct).toFixed(2)}%` : "-",
      },
    ],
    []
  );

  let description = "加载中...";
  if (isError) description = "无法获取数据";
  if (!isLoading && !isError && data.length === 0) description = "暂无候选";

  return (
    <Card
      title="候选池"
      extra={<Typography.Text style={{ color: "#94a3b8" }}>{description}</Typography.Text>}
    >
      <Table
        rowKey="ts_code"
        columns={columns}
        dataSource={data}
        loading={isLoading}
        pagination={false}
        scroll={{ x: 800 }}
      />
    </Card>
  );
}
