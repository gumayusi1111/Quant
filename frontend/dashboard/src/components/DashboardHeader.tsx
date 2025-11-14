"use client";

import { Typography } from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";

interface DashboardHeaderProps {
  regime?: string;
  description?: string;
}

export function DashboardHeader({
  regime,
  description = "市场数据将自动从后端读取，若暂无记录会显示“未知”。",
}: DashboardHeaderProps) {
  const [currentTime, setCurrentTime] = useState<string>("");

  useEffect(() => {
    const update = () => setCurrentTime(dayjs().format("YYYY/MM/DD HH:mm:ss"));
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="app-header">
      <Typography.Title level={3} style={{ color: "#111827" }}>
        今日概览 · {currentTime || "--"}
      </Typography.Title>
      <Typography.Text style={{ color: "#111827", fontWeight: 500 }}>
        市场环境：{regime || "未知"} · {description}
      </Typography.Text>
    </header>
  );
}
