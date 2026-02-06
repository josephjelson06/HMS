import { apiFetch } from "@/lib/api/client";
import type {
  Incident,
  IncidentCreate,
  IncidentListResponse,
  IncidentUpdate
} from "@/lib/types/incidents";

export const hotelIncidentsApi = {
  list: (params?: { page?: number; limit?: number; search?: string; status?: string; severity?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.search) query.set("search", params.search);
    if (params?.status) query.set("status", params.status);
    if (params?.severity) query.set("severity", params.severity);
    const qs = query.toString();
    return apiFetch<IncidentListResponse>(`/hotel/incidents${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => apiFetch<Incident>(`/hotel/incidents/${id}`),
  create: (payload: IncidentCreate) =>
    apiFetch<Incident>("/hotel/incidents", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: IncidentUpdate) =>
    apiFetch<Incident>(`/hotel/incidents/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/hotel/incidents/${id}`, { method: "DELETE" })
};
