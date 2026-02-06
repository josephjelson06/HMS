import { apiFetch } from "@/lib/api/client";
import type { Profile, ProfileUpdate } from "@/lib/types/profile";

export const hotelProfileApi = {
  get: () => apiFetch<Profile>("/hotel/profile"),
  update: (payload: ProfileUpdate) =>
    apiFetch<Profile>("/hotel/profile", { method: "PUT", body: JSON.stringify(payload) })
};
