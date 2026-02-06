"use client";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { RoleEditor } from "@/components/features/roles/role-editor";
import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";

export default function AdminRoleCreatePage() {
  return (
    <PermissionGuard
      permission="admin:roles:create"
      fallback={
        <AccessDeniedState message="You do not have permission to create admin roles." />
      }
    >
      <RoleEditor scope="admin" />
    </PermissionGuard>
  );
}
