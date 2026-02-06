import { apiFetch } from "@/lib/api/client";
import type { HelpdeskCreate, HelpdeskTicket } from "@/lib/types/helpdesk";

export const hotelHelpdeskApi = {
  list: (limit = 20) => apiFetch<HelpdeskTicket[]>(`/hotel/helpdesk?limit=${limit}`),
  create: (payload: HelpdeskCreate) =>
    apiFetch<HelpdeskTicket>("/hotel/helpdesk", { method: "POST", body: JSON.stringify(payload) })
};
