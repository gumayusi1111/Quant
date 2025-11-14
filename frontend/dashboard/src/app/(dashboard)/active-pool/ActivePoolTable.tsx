"use client";

import { useMemo, useState } from "react";
import { Input, Select, Space, Table } from "antd";
import type { ColumnsType } from "antd/es/table";

type ActivePoolRow = Record<string, string>;

interface ActivePoolTableProps {
  data: ActivePoolRow[];
}

interface ProcessedRow extends ActivePoolRow {
  meanAmount: number | null;
  tradeRatio: number | null;
  rangeRatio: number | null;
  listedDays: number | null;
  recentClose: number | null;
}

const LIQUIDITY_OPTIONS = [
  { label: "全部成交额", value: 0 },
  { label: "60日均额 ≥ 3000万", value: 3_000_000 },
  { label: "60日均额 ≥ 5000万", value: 5_000_000 },
  { label: "60日均额 ≥ 1亿", value: 10_000_000 },
];

const RATIO_OPTIONS = [
  { label: "不限交易日占比", value: 0 },
  { label: "≥ 80%", value: 0.8 },
  { label: "≥ 90%", value: 0.9 },
  { label: "满勤 (≈100%)", value: 0.99 },
];

function toNumber(value: string | undefined): number | null {
  if (value === undefined) return null;
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

function formatAmount(value: number | null) {
  if (value === null) return "-";
  if (value >= 1e8) {
    return `${(value / 1e8).toFixed(2)} 亿`;
  }
  if (value >= 1e4) {
    return `${(value / 1e4).toFixed(1)} 万`;
  }
  return value.toFixed(0);
}

function formatPercent(value: number | null, digits = 1) {
  if (value === null) return "-";
  return `${(value * 100).toFixed(digits)}%`;
}

export function ActivePoolTable({ data }: ActivePoolTableProps) {
  const [keyword, setKeyword] = useState("");
  const [liquidity, setLiquidity] = useState<number>(0);
  const [ratio, setRatio] = useState<number>(0);
  const [pageSize, setPageSize] = useState(20);

  const processed: ProcessedRow[] = useMemo(() => {
    return data
      .map((row) => ({
        ...row,
        meanAmount: toNumber(row.mean_amount_60),
        tradeRatio: toNumber(row.trade_days_ratio_60),
        rangeRatio: toNumber(row.median_range_60),
        listedDays: toNumber(row.listed_days),
        recentClose: toNumber(row.recent_close),
      }))
      .filter((row) => {
        if (!keyword) return true;
        const lower = keyword.toLowerCase();
        return (
          row.ts_code?.toLowerCase().includes(lower) ||
          row.name?.toLowerCase().includes(lower)
        );
      })
      .filter((row) => {
        if (!row.meanAmount && liquidity > 0) return false;
        return row.meanAmount === null || row.meanAmount >= liquidity;
      })
      .filter((row) => {
        if (!row.tradeRatio && ratio > 0) return false;
        return row.tradeRatio === null || row.tradeRatio >= ratio;
      });
  }, [data, keyword, liquidity, ratio]);

  const columns: ColumnsType<ProcessedRow> = [
    { title: "代码", dataIndex: "ts_code", width: 140 },
    { title: "名称", dataIndex: "name", width: 180 },
    {
      title: "60日均成交额",
      dataIndex: "meanAmount",
      width: 160,
      render: (value: number | null) => formatAmount(value),
    },
    {
      title: "60日交易日占比",
      dataIndex: "tradeRatio",
      width: 160,
      render: (value: number | null) => formatPercent(value),
    },
    {
      title: "60日日内振幅(中位)",
      dataIndex: "rangeRatio",
      width: 180,
      render: (value: number | null) => formatPercent(value, 2),
    },
    {
      title: "最新收盘价",
      dataIndex: "recentClose",
      width: 140,
      render: (value: number | null) => (value === null ? "-" : value.toFixed(3)),
    },
    {
      title: "上市天数",
      dataIndex: "listedDays",
      width: 120,
      render: (value: number | null) => (value === null ? "-" : value),
    },
  ];

  return (
    <>
      <Space direction="vertical" size="middle" style={{ width: "100%", marginBottom: 16 }}>
        <Space wrap>
          <Input.Search
            placeholder="搜索代码或名称"
            allowClear
            onChange={(e) => setKeyword(e.target.value.trim())}
            style={{ minWidth: 260 }}
          />
          <Select
            value={liquidity}
            options={LIQUIDITY_OPTIONS}
            style={{ width: 200 }}
            onChange={setLiquidity}
          />
          <Select
            value={ratio}
            options={RATIO_OPTIONS}
            style={{ width: 200 }}
            onChange={setRatio}
          />
        </Space>
      </Space>
      <Table
        rowKey={(row) => row.ts_code || row.name || Math.random().toString()}
        columns={columns}
        dataSource={processed}
        pagination={{
          pageSize,
          showSizeChanger: true,
          pageSizeOptions: ["10", "20", "50", "100"],
          onChange: (_page, size) => setPageSize(size || 20),
        }}
        scroll={{ x: 980 }}
      />
    </>
  );
}
