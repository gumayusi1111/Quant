import { ReactNode } from "react";
import { AppSidebar } from "@/components/AppSidebar";
import { DashboardHeader } from "@/components/DashboardHeader";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <AppSidebar />
      <div className="app-main">
        <DashboardHeader regime="自动检测中" />
        <main className="content-shell">{children}</main>
      </div>
    </div>
  );
}
