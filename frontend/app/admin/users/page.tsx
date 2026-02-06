"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";
import { ConfirmDialog } from "@/components/ui/composed/confirm-dialog";
import { DataTable } from "@/components/ui/composed/data-table";
import { DirectoryTableCard } from "@/components/ui/composed/directory-table-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { FormModal } from "@/components/ui/composed/form-modal";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { TableActionCell } from "@/components/ui/composed/table-action-cell";
import { Button } from "@/components/ui/primitives/button";
import { DataToolbar } from "@/components/ui/primitives/data-toolbar";
import { Field } from "@/components/ui/primitives/field";
import { Pagination } from "@/components/ui/primitives/pagination";
import { SelectInput } from "@/components/ui/primitives/select-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { adminUsersApi } from "@/lib/api/admin/users";
import type { AdminRole, AdminUser } from "@/lib/types/user";

const defaultForm = {
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  role_id: "",
  is_active: true
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<AdminUser | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchData = useCallback(async (nextPage = page) => {
    setLoading(true);
    setError(null);
    try {
      const [usersData, rolesData] = await Promise.all([adminUsersApi.list(nextPage, limit), adminUsersApi.roles()]);
      setUsers(usersData.items);
      setRoles(rolesData);
      setPage(usersData.pagination.page);
      setTotal(usersData.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, [limit, page]);

  useEffect(() => {
    void fetchData(page);
  }, [fetchData, page]);

  const handleChange = (field: keyof typeof defaultForm, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setForm(defaultForm);
    setEditing(null);
  };

  const openCreate = () => {
    resetForm();
    setFormOpen(true);
  };

  const payload = useMemo(
    () => ({
      email: form.email,
      password: form.password || undefined,
      first_name: form.first_name || undefined,
      last_name: form.last_name || undefined,
      role_id: form.role_id,
      is_active: form.is_active
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await adminUsersApi.update(editing.id, payload);
        toast.success("User updated");
      } else {
        if (!payload.password) {
          setError("Password is required for new users");
          return;
        }
        await adminUsersApi.create({
          email: payload.email,
          password: payload.password,
          first_name: payload.first_name,
          last_name: payload.last_name,
          role_id: payload.role_id,
          is_active: payload.is_active
        });
        toast.success("User created");
      }
      setFormOpen(false);
      resetForm();
      await fetchData(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save user";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (user: AdminUser) => {
    const roleMatch = roles.find((role) => role.name === user.roles[0]);
    setEditing(user);
    setForm({
      email: user.email,
      password: "",
      first_name: user.first_name ?? "",
      last_name: user.last_name ?? "",
      role_id: roleMatch?.id ?? "",
      is_active: user.is_active
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await adminUsersApi.remove(pendingDelete.id);
      toast.success("User deleted");
      setPendingDelete(null);
      await fetchData(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete user";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="admin:users:read"
      fallback={<AccessDeniedState message="You do not have permission to view admin users." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Admin Users"
          description="Manage platform administrators and their roles."
          count={total}
          countLabel="Users"
          rightSlot={
            <PermissionGuard permission="admin:users:create">
              <Button variant="primary" onClick={openCreate}>
                Add User
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Admin Directory"
          table={
            <>
              <DataToolbar
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchData(page)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading users..." className="mt-3" />
              ) : users.length === 0 ? (
                <EmptyState description="No admin users yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      { key: "email", header: "Email", cellClassName: "font-medium", render: (user) => user.email },
                      {
                        key: "name",
                        header: "Name",
                        render: (user) => [user.first_name, user.last_name].filter(Boolean).join(" ") || "-"
                      },
                      { key: "role", header: "Role", render: (user) => user.roles[0] ?? "-" },
                      { key: "status", header: "Status", render: (user) => (user.is_active ? "Active" : "Inactive") },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (user) => (
                          <TableActionCell>
                            <PermissionGuard permission="admin:users:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(user)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="admin:users:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(user)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={users}
                    rowKey={(user) => user.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "admin:users:update" : "admin:users:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Admin User" : "Add Admin User"}
          description="Manage internal admin accounts and role assignment."
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Email" required>
              <TextInput
                value={form.email}
                onChange={(event) => handleChange("email", event.target.value)}
                placeholder="admin@company.com"
                required
              />
            </Field>
            <Field label={`Password${editing ? " (optional)" : ""}`}>
              <TextInput
                value={form.password}
                onChange={(event) => handleChange("password", event.target.value)}
                placeholder={editing ? "Leave blank to keep" : "********"}
                type="password"
              />
            </Field>
            <Field label="First Name">
              <TextInput
                value={form.first_name}
                onChange={(event) => handleChange("first_name", event.target.value)}
                placeholder="Alex"
              />
            </Field>
            <Field label="Last Name">
              <TextInput
                value={form.last_name}
                onChange={(event) => handleChange("last_name", event.target.value)}
                placeholder="Morgan"
              />
            </Field>
            <Field label="Role" required>
              <SelectInput value={form.role_id} onChange={(event) => handleChange("role_id", event.target.value)} required>
                <option value="">Select a role</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.display_name}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <div className="flex items-center gap-2 pt-8">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => handleChange("is_active", event.target.checked)}
              />
              <span className="text-sm">Active</span>
            </div>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create User"}
              </Button>
            </div>
          </form>
        </FormModal>
      </PermissionGuard>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        onOpenChange={(open) => {
          if (!open) setPendingDelete(null);
        }}
        title="Delete admin user"
        description={pendingDelete ? `Delete ${pendingDelete.email}? This action cannot be undone.` : "Delete user?"}
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
