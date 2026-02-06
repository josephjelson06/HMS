import { apiFetch } from "@/lib/api/client";
import type { Subscription, SubscriptionCreate, SubscriptionListResponse, SubscriptionUpdate } from "@/lib/types/subscriptions";

export const adminSubscriptionsApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<SubscriptionListResponse>(`/admin/subscriptions?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<Subscription>(`/admin/subscriptions/${id}`),
  create: (payload: SubscriptionCreate) =>
    apiFetch<Subscription>("/admin/subscriptions", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: SubscriptionUpdate) =>
    apiFetch<Subscription>(`/admin/subscriptions/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/subscriptions/${id}`, { method: "DELETE" })
};
