"use client";

import { Card, Space, Button, Tag, message, Typography } from "antd";
import dayjs from "dayjs";
import { useTaskStatus, useTriggerTask } from "@/hooks/useTaskStatus";
import type { TaskName } from "@/lib/task-api";

const TASK_CONFIG: Array<{
  key: TaskName;
  label: string;
  description: string;
}> = [
  {
    key: "full_pool",
    label: "刷新全量池",
    description: "重新拉取全市场 ETF 基础信息（受刷新间隔限制）。",
  },
  {
    key: "daily",
    label: "增量日线+指标",
    description: "仅补当前缺失的交易日，并同步计算指标。",
  },
  {
    key: "backfill_daily",
    label: "全量日线（慢）",
    description: "首次或特殊情况使用，重新拉取全部历史并计算指标。",
  },
  {
    key: "daily_routine",
    label: "日常一键",
    description: "顺序执行：日线增量 → 活跃池/市场 → 生成候选池。",
  },
  {
    key: "watchlist",
    label: "生成候选池",
    description: "运行 watchlist pipeline，更新观察池。",
  },
  {
    key: "auto",
    label: "一键 Auto",
    description: "执行完整 nightly 流水线（含所有步骤）。",
  },
];

function formatTime(value?: string | null) {
  if (!value) return "-";
  return dayjs(value).format("MM/DD HH:mm:ss");
}

export function TaskControlPanel() {
  const { data, isLoading } = useTaskStatus();
  const trigger = useTriggerTask();

  const handleTrigger = async (task: TaskName) => {
    try {
      await trigger.mutateAsync(task);
      const cfg = TASK_CONFIG.find((item) => item.key === task);
      message.success(`${cfg?.label || task} 已启动`);
    } catch (error) {
      const text = error instanceof Error ? error.message : "触发失败";
      message.error(text);
    }
  };

  return (
    <Card title="任务控制" loading={isLoading} style={{ marginBottom: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        {TASK_CONFIG.map(({ key: task, label, description }) => {
          const status = data?.[task];
          const tagColor =
            status?.status === "success"
              ? "green"
              : status?.status === "running"
              ? "processing"
              : status?.status === "failed"
              ? "red"
              : "default";
          return (
            <div
              key={task}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 12,
              }}
            >
              <div>
                <div style={{ fontWeight: 600 }}>{label}</div>
                <Typography.Text style={{ display: "block", color: "#6b7280" }}>
                  {description}
                </Typography.Text>
                <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>
                  状态：
                  <Tag color={tagColor} style={{ marginInline: 8 }}>
                    {status?.status || "idle"}
                  </Tag>
                  最近开始：{formatTime(status?.started_at)} · 最近完成：
                  {formatTime(status?.finished_at)}
                </div>
              </div>
              <Button
                type="primary"
                disabled={status?.status === "running" || trigger.isLoading}
                loading={trigger.isLoading && trigger.variables === task}
                onClick={() => handleTrigger(task)}
              >
                立即执行
              </Button>
            </div>
          );
        })}
      </Space>
    </Card>
  );
}
