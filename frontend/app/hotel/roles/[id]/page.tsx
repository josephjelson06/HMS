"use client";

import { useParams } from "next/navigation";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { RoleEditor } from "@/components/features/roles/role-editor";
import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";

export default function HotelRoleDetailPage() {
  const params = useParams<{ id: string }>();

  return (
    <PermissionGuard
      permission="hotel:roles:update"
      fallback={
        <AccessDeniedState message="You do not have permission to edit hotel roles." />
      }
    >
      <RoleEditor scope="hotel" roleId={params.id} />
    </PermissionGuard>
  );
}
