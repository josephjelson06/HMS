"use client";

import { useParams } from "next/navigation";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { RoleEditor } from "@/components/features/roles/role-editor";
import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";

export default function AdminRoleDetailPage() {
  const params = useParams<{ id: string }>();

  return (
    <PermissionGuard
      permission="admin:roles:update"
      fallback={
        <AccessDeniedState message="You do not have permission to edit admin roles." />
      }
    >
      <RoleEditor scope="admin" roleId={params.id} />
    </PermissionGuard>
  );
}
