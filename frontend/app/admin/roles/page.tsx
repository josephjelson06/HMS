"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { ConfirmDialog } from "@/components/ui/composed/confirm-dialog";
import { DataTable } from "@/components/ui/composed/data-table";
import { DirectoryTableCard } from "@/components/ui/composed/directory-table-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { TableActionCell } from "@/components/ui/composed/table-action-cell";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/primitives/button";
import { adminRolesApi } from "@/lib/api/admin/roles";
import type { AdminRole } from "@/lib/types/roles";

export default function AdminRolesPage() {
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<AdminRole | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);

  const fetchRoles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminRolesApi.list();
      setRoles(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load roles");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchRoles();
  }, [fetchRoles]);

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    if (pendingDelete.is_system) {
      setPendingDelete(null);
      setError("System roles cannot be deleted");
      return;
    }
    setConfirmBusy(true);
    try {
      await adminRolesApi.remove(pendingDelete.id);
      toast.success("Role deleted");
      setPendingDelete(null);
      await fetchRoles();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete role";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="admin:roles:read"
      fallback={
        <GlassCard className="p-6">
          <h2 className="text-2xl">Access denied</h2>
          <p className="mt-2 text-sm text-[color:var(--color-text-muted)]">
            You do not have permission to view admin roles.
          </p>
        </GlassCard>
      }
    >
      <div className="space-y-6">
        <PageHeader
          title="Admin Roles"
          description="Manage role definitions and open matrix editor for granular permissions."
          count={roles.length}
          countLabel="Roles"
          rightSlot={
            <PermissionGuard permission="admin:roles:create">
              <Link href="/admin/roles/new" className="ui-btn ui-btn-primary ui-btn-sm ui-anim">
                Add Role
              </Link>
            </PermissionGuard>
          }
        />

        {error ? <InlineAlert tone="error" message={error} /> : null}

        {loading ? (
          <InlineAlert tone="info" message="Loading roles..." />
        ) : roles.length === 0 ? (
          <EmptyState description="No roles created yet." />
        ) : (
          <DirectoryTableCard
            title="Role Directory"
            table={
              <DataTable
                columns={[
                  {
                    key: "role",
                    header: "Role",
                    cellClassName: "font-medium",
                    render: (role) => role.display_name
                  },
                  {
                    key: "key",
                    header: "Key",
                    cellClassName: "text-[color:var(--color-text-muted)]",
                    render: (role) => role.name
                  },
                  {
                    key: "system",
                    header: "System",
                    render: (role) => (role.is_system ? "Yes" : "No")
                  },
                  {
                    key: "permissions",
                    header: "Permissions",
                    render: (role) => role.permissions.length
                  },
                  {
                    key: "updated",
                    header: "Updated",
                    cellClassName: "text-[color:var(--color-text-muted)]",
                    render: (role) =>
                      role.updated_at ? new Date(role.updated_at).toLocaleString() : "N/A"
                  },
                  {
                    key: "actions",
                    header: "Actions",
                    render: (role) => (
                      <TableActionCell>
                        <PermissionGuard permission="admin:roles:update">
                          <Link
                            href={`/admin/roles/${role.id}`}
                            className="ui-btn ui-btn-outline ui-btn-sm ui-anim"
                          >
                            {role.is_system ? "View" : "Edit"}
                          </Link>
                        </PermissionGuard>
                        <PermissionGuard permission="admin:roles:delete">
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => setPendingDelete(role)}
                            disabled={role.is_system}
                          >
                            Delete
                          </Button>
                        </PermissionGuard>
                      </TableActionCell>
                    )
                  }
                ]}
                rows={roles}
                rowKey={(role) => role.id}
              />
            }
          />
        )}
      </div>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        onOpenChange={(open) => {
          if (!open) setPendingDelete(null);
        }}
        title="Delete role"
        description={
          pendingDelete
            ? `Delete ${pendingDelete.display_name}? This action cannot be undone.`
            : "Delete role?"
        }
        confirmText="Delete"
        tone="danger"
        busy={confirmBusy}
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
