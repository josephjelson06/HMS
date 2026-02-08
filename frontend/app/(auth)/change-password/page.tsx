"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { authApi } from "@/lib/api/auth";
import { useAuth } from "@/lib/hooks/use-auth";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { Button } from "@/components/ui/primitives/button";
import { Field } from "@/components/ui/primitives/field";
import { TextInput } from "@/components/ui/primitives/text-input";

function getDashboardRoute(userType: string | undefined): string {
  if (userType === "platform" || userType === "admin") {
    return "/admin/dashboard";
  }
  return "/hotel/dashboard";
}

export default function ChangePasswordPage() {
  const router = useRouter();
  const { user, loading, mustResetPassword, refresh } = useAuth();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const dashboardRoute = useMemo(() => getDashboardRoute(user?.user_type), [user?.user_type]);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
      return;
    }

    if (!loading && user && !mustResetPassword) {
      router.replace(dashboardRoute);
    }
  }, [dashboardRoute, loading, mustResetPassword, router, user]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });
      await refresh();
      setSuccess(response.message);
      router.push(dashboardRoute);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unable to change password";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !user) {
    return null;
  }

  return (
    <div className="glass-card auth-card">
      <div className="space-y-6">
        <div>
          <h1 className="mt-1 text-3xl">Reset your password</h1>
          <p className="text-sm text-[color:var(--color-text-muted)]">
            You must change your password before accessing HMS.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Current Password">
            <TextInput
              type="password"
              required
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              placeholder="********"
            />
          </Field>
          <Field label="New Password">
            <TextInput
              type="password"
              required
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="********"
            />
          </Field>
          <Field label="Confirm New Password">
            <TextInput
              type="password"
              required
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="********"
            />
          </Field>

          {error ? <InlineAlert tone="error" message={error} /> : null}
          {success ? <InlineAlert tone="success" message={success} /> : null}

          <Button type="submit" variant="primary" className="w-full" disabled={submitting}>
            {submitting ? "Updating..." : "Change password"}
          </Button>
        </form>
      </div>
    </div>
  );
}
