"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchTaskStatuses, triggerTask, TaskName } from "@/lib/task-api";

export function useTaskStatus() {
  return useQuery({
    queryKey: ["task-status"],
    queryFn: fetchTaskStatuses,
    refetchInterval: 5000,
  });
}

export function useTriggerTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: triggerTask,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["task-status"] }),
  });
}
