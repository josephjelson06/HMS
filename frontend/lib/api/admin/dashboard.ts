import { apiFetch } from "@/lib/api/client";
import type { AdminDashboardSummary } from "@/lib/types/dashboard";

export const adminDashboardApi = {
  summary: () => apiFetch<AdminDashboardSummary>("/admin/dashboard/summary")
};
