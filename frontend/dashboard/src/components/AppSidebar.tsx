"use client";

import { Menu } from "antd";
import { usePathname, useRouter } from "next/navigation";
import {
  PieChartOutlined,
  TableOutlined,
  EyeOutlined,
  ThunderboltOutlined,
  ClusterOutlined,
} from "@ant-design/icons";

const items = [
  { key: "/overview", icon: <PieChartOutlined />, label: "仪表盘" },
  { key: "/full-pool", icon: <TableOutlined />, label: "全量池" },
  { key: "/active-pool", icon: <ClusterOutlined />, label: "活跃池" },
  { key: "/watchlist", icon: <TableOutlined />, label: "候选池" },
  { key: "/pool", icon: <EyeOutlined />, label: "观察池" },
  { key: "/execution", icon: <ThunderboltOutlined />, label: "执行池" },
];

export function AppSidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const selectedKey =
    items.find((item) => pathname?.startsWith(item.key))?.key ?? "/overview";
  return (
    <div className="sidebar">
      <div className="sidebar__title">Quant Dashboard</div>
      <Menu
        theme="light"
        mode="inline"
        selectedKeys={[selectedKey]}
        items={items}
        onSelect={({ key }) => {
          router.push(key.toString());
        }}
        className="sidebar-menu"
      />
    </div>
  );
}
