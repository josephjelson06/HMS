"use client";

import { useCallback, useEffect, useState } from "react";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { CrudFormCard } from "@/components/ui/composed/crud-form-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { SectionCard } from "@/components/ui/composed/section-card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/primitives/button";
import { Field } from "@/components/ui/primitives/field";
import { TextInput } from "@/components/ui/primitives/text-input";
import { adminProfileApi } from "@/lib/api/admin/profile";
import { useAuth } from "@/lib/hooks/use-auth";
import type { Profile } from "@/lib/types/profile";

const defaultForm = {
  first_name: "",
  last_name: "",
  current_password: "",
  new_password: ""
};

export default function AdminProfilePage() {
  const { refresh } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminProfileApi.get();
      setProfile(data);
      setForm({
        first_name: data.first_name ?? "",
        last_name: data.last_name ?? "",
        current_password: "",
        new_password: ""
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load profile");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  const handleChange = (field: keyof typeof defaultForm, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      await adminProfileApi.update({
        first_name: form.first_name || undefined,
        last_name: form.last_name || undefined,
        current_password: form.current_password || undefined,
        new_password: form.new_password || undefined
      });
      await refresh();
      setSuccess("Profile updated successfully.");
      setForm((prev) => ({ ...prev, current_password: "", new_password: "" }));
      await loadProfile();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    }
  };

  return (
    <PermissionGuard
      permission="admin:profile:read"
      fallback={
        <GlassCard className="p-6">
          <h2 className="text-2xl">Access denied</h2>
          <p className="mt-2 text-sm text-[color:var(--color-text-muted)]">
            You do not have permission to view your profile.
          </p>
        </GlassCard>
      }
    >
      <div className="space-y-6">
        <PageHeader title="My Profile" description="Manage your account details and password." />

        {loading ? (
          <InlineAlert tone="info" message="Loading profile..." />
        ) : !profile ? (
          <EmptyState description="Profile not available." />
        ) : (
          <>
            <SectionCard title="Account Info">
              <div className="grid gap-4 md:grid-cols-2 text-sm">
                <p>
                  <span className="text-[color:var(--color-text-muted)]">Email:</span> {profile.email}
                </p>
                <p>
                  <span className="text-[color:var(--color-text-muted)]">Role:</span>{" "}
                  <span className="capitalize">{profile.user_type}</span>
                </p>
              </div>
            </SectionCard>

            <PermissionGuard permission="admin:profile:update">
              <CrudFormCard title="Update Profile">
                <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
                  <Field label="First Name">
                    <TextInput
                      value={form.first_name}
                      onChange={(event) => handleChange("first_name", event.target.value)}
                      placeholder="First name"
                    />
                  </Field>
                  <Field label="Last Name">
                    <TextInput
                      value={form.last_name}
                      onChange={(event) => handleChange("last_name", event.target.value)}
                      placeholder="Last name"
                    />
                  </Field>
                  <Field label="Current Password">
                    <TextInput
                      type="password"
                      value={form.current_password}
                      onChange={(event) => handleChange("current_password", event.target.value)}
                      placeholder="********"
                    />
                  </Field>
                  <Field label="New Password">
                    <TextInput
                      type="password"
                      value={form.new_password}
                      onChange={(event) => handleChange("new_password", event.target.value)}
                      placeholder="********"
                    />
                  </Field>
                  <div className="md:col-span-2">
                    <Button type="submit" variant="primary">
                      Save Changes
                    </Button>
                  </div>
                </form>
              </CrudFormCard>
            </PermissionGuard>

            {error ? <InlineAlert tone="error" message={error} /> : null}
            {success ? <InlineAlert tone="success" message={success} /> : null}
          </>
        )}
      </div>
    </PermissionGuard>
  );
}
