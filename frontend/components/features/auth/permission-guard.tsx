"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";
import { useAuth } from "@/lib/hooks/use-auth";
import type { UserType } from "@/lib/types/auth";
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
  userType: UserType;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const router = useRouter();
  const { user, loading, mustResetPassword } = useAuth();

  useEffect(() => {
    if (!loading && user && mustResetPassword) {
      router.replace("/change-password");
    }
  }, [loading, mustResetPassword, router, user]);

  if (loading) return null;
  if (user && mustResetPassword) return null;

  const matchesUserType = (actual: UserType, expected: UserType): boolean => {
    if (expected === "platform") return actual === "platform" || actual === "admin";
    if (expected === "admin") return actual === "admin" || actual === "platform";
    return actual === "hotel";
  };

  if (user && matchesUserType(user.user_type, userType)) {
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
