"use client";

import { Alert, Card, Spin } from "antd";
import { useActivePool } from "@/hooks/useActivePool";
import { ActivePoolMetaCard } from "./ActivePoolMetaCard";
import { ActivePoolTable } from "./ActivePoolTable";

export function ActivePoolView() {
  const { data, isLoading, isError } = useActivePool();
  const rows = data?.data ?? [];
  const meta = data?.meta;

  return (
    <section className="page-panel">
      <ActivePoolMetaCard
        updatedAt={meta?.updatedAt ?? null}
        total={meta?.total ?? rows.length}
        avgAmount60={meta?.avgAmount60}
        avgTradeRatio60={meta?.avgTradeRatio60}
        avgRange60={meta?.avgRange60}
      />
      {isError && <Alert message="无法获取活跃池数据" type="error" showIcon closable />}
      <Spin spinning={isLoading} tip="加载中...">
        <Card bordered={false} bodyStyle={{ padding: 0 }}>
          <ActivePoolTable data={rows} />
        </Card>
      </Spin>
    </section>
  );
}
