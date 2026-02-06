import { apiFetch } from "@/lib/api/client";
import type { Profile, ProfileUpdate } from "@/lib/types/profile";

export const adminProfileApi = {
  get: () => apiFetch<Profile>("/admin/profile"),
  update: (payload: ProfileUpdate) =>
    apiFetch<Profile>("/admin/profile", { method: "PUT", body: JSON.stringify(payload) })
};
