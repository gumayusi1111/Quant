const TASK_API_BASE =
  process.env.NEXT_PUBLIC_TASK_API_BASE || "http://127.0.0.1:8000";

export type TaskName =
  | "full_pool"
  | "backfill_daily"
  | "daily"
  | "daily_routine"
  | "watchlist"
  | "auto";

export interface TaskStatusEntry {
  task: TaskName;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds?: number | null;
  message?: string | null;
}

export async function fetchTaskStatuses(): Promise<Record<string, TaskStatusEntry>> {
  const res = await fetch(`${TASK_API_BASE}/tasks/status`);
  if (!res.ok) {
    throw new Error("无法获取任务状态");
  }
  return res.json();
}

export async function triggerTask(task: TaskName): Promise<void> {
  const res = await fetch(`${TASK_API_BASE}/tasks/${task}`, {
    method: "POST",
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload?.detail || `任务 ${task} 启动失败`);
  }
}
