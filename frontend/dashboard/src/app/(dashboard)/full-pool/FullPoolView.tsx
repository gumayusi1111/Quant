"use client";

import { Alert, Card, Spin } from "antd";
import { useFullPool } from "@/hooks/useFullPool";
import { FullPoolStats } from "./FullPoolStats";
import { FullPoolTable } from "./FullPoolTable";
import { FullPoolMetaCard } from "./FullPoolMetaCard";
import { isDelisted, isSuspended } from "./utils";

export function FullPoolView() {
  const { data, isLoading, isError } = useFullPool();
  const rows = data?.data ?? [];
  const meta = data?.meta;

  const stats = {
    total: rows.length,
    suspended: rows.filter(isSuspended).length,
    delisted: rows.filter(isDelisted).length,
  };

  return (
    <section className="page-panel">
      <FullPoolMetaCard
        updatedAt={meta?.updatedAt || null}
        newWithin30d={meta?.newWithin30d}
        anomalyCount={meta?.anomalyCount}
      />
      <FullPoolStats {...stats} />
      {isError && <Alert message="无法获取全量池数据" type="error" showIcon closable />}
      <Spin spinning={isLoading} tip="加载中...">
        <Card bordered={false} bodyStyle={{ padding: 0 }}>
          <FullPoolTable data={rows} />
        </Card>
      </Spin>
    </section>
  );
}
