import { apiFetch } from "@/lib/api/client";
import type { Plan, PlanCreate, PlanListResponse, PlanUpdate } from "@/lib/types/plans";

export const adminPlansApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<PlanListResponse>(`/admin/plans?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<Plan>(`/admin/plans/${id}`),
  create: (payload: PlanCreate) =>
    apiFetch<Plan>("/admin/plans", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: PlanUpdate) =>
    apiFetch<Plan>(`/admin/plans/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/plans/${id}`, { method: "DELETE" })
};
