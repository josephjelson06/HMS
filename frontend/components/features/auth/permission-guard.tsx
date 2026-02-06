"use client";

import type { ReactNode } from "react";

import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";
import { useAuth } from "@/lib/hooks/use-auth";
import { hasPermission } from "@/lib/utils/permissions";

export function PermissionGuard({
  permission,
  children,
  fallback = null
}: {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { permissions, loading } = useAuth();

  if (loading) return null;
  if (hasPermission(permissions, permission)) {
    return <>{children}</>;
  }

  return <>{fallback}</>;
}

export function UserTypeGuard({
  userType,
  children,
  fallback = null
}: {
  userType: "admin" | "hotel";
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (user && user.user_type === userType) {
    return <>{children}</>;
  }

  return (
    <div className="auth-layout">
      <AccessDeniedState
        className="auth-card"
        message="You do not have access to this workspace."
      >
        {fallback}
      </AccessDeniedState>
    </div>
  );
}
