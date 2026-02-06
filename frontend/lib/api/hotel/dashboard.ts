import { apiFetch } from "@/lib/api/client";
import type { HotelDashboardSummary } from "@/lib/types/dashboard";

export const hotelDashboardApi = {
  summary: () => apiFetch<HotelDashboardSummary>("/hotel/dashboard/summary")
};
