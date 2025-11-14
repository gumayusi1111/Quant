"use client";

import { useMemo, useState } from "react";
import { Input, Select, Space, Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import {
  isDelisted,
  isSuspended,
  resolveStatus,
  resolveExchange,
  resolveDelistDate,
  PoolRow,
} from "./utils";

interface FullPoolTableProps {
  data: PoolRow[];
}

const SEARCH_FIELDS = [
  "ts_code",
  "name",
  "fullname",
  "exchange",
  "market",
] as const;

type ProcessedRow = PoolRow & {
  __status: string;
  __exchange: string;
  __delist: string;
};

const STATUS_OPTIONS = [
  { label: "全部", value: "all" },
  { label: "在市", value: "active" },
  { label: "停牌", value: "suspended" },
  { label: "退市", value: "delisted" },
];

export function FullPoolTable({ data }: FullPoolTableProps) {
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [pageSize, setPageSize] = useState(20);

  const processed: ProcessedRow[] = useMemo(() => {
    return data
      .filter((row) => {
        if (!keyword) return true;
        const lower = keyword.toLowerCase();
        return SEARCH_FIELDS.some((field) => {
          const raw = row[field as keyof PoolRow];
          const text = raw === undefined || raw === null ? "" : String(raw);
          return text.toLowerCase().includes(lower);
        });
      })
      .filter((row) => {
        if (statusFilter === "all") return true;
        if (statusFilter === "suspended") return isSuspended(row);
        if (statusFilter === "delisted") return isDelisted(row);
        return !isSuspended(row) && !isDelisted(row);
      })
      .map((row) => ({
        ...row,
        __status: resolveStatus(row),
        __exchange: resolveExchange(row),
        __delist: resolveDelistDate(row),
      }));
  }, [data, keyword, statusFilter]);

  const columns: ColumnsType<ProcessedRow> = [
    { title: "代码", dataIndex: "ts_code", width: 140 },
    { title: "名称", dataIndex: "name", width: 180 },
    {
      title: "交易所",
      dataIndex: "__exchange",
      width: 120,
      render: (value: string) => value || "-",
    },
    { title: "上市日期", dataIndex: "list_date", width: 140 },
    {
      title: "退市日期",
      dataIndex: "__delist",
      width: 140,
      render: (value: string) => value || "-",
    },
    {
      title: "状态",
      dataIndex: "__status",
      width: 120,
      render: (value) => {
        const color = value === "退市" ? "red" : value === "停牌" ? "orange" : "green";
        return <Tag color={color}>{value}</Tag>;
      },
    },
  ];

  return (
    <>
      <Space direction="vertical" size="middle" style={{ width: "100%", marginBottom: 16 }}>
        <Space wrap>
          <Input.Search
            placeholder="搜索代码/名称"
            allowClear
            onChange={(e) => setKeyword(e.target.value.trim())}
            style={{ minWidth: 260 }}
          />
          <Select
            value={statusFilter}
            options={STATUS_OPTIONS}
            onChange={setStatusFilter}
            style={{ width: 160 }}
          />
        </Space>
      </Space>
      <Table
        rowKey={(row) => row.ts_code || row.name || String(Math.random())}
        columns={columns}
        dataSource={processed}
        pagination={{
          pageSize,
          showSizeChanger: true,
          pageSizeOptions: ["10", "20", "50", "100"],
          onChange: (_page, size) => setPageSize(size || 20),
        }}
        scroll={{ x: 900 }}
      />
    </>
  );
}
