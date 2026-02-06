"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/layout/primitives/page-header";
import { CrudFormCard } from "@/components/ui/composed/crud-form-card";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { ResponsiveTableContainer } from "@/components/ui/composed/responsive-table-container";
import { SectionCard } from "@/components/ui/composed/section-card";
import { Badge } from "@/components/ui/primitives/badge";
import { Button } from "@/components/ui/primitives/button";
import { Field } from "@/components/ui/primitives/field";
import { TextAreaInput } from "@/components/ui/primitives/textarea-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { adminRolesApi } from "@/lib/api/admin/roles";
import { hotelRolesApi } from "@/lib/api/hotel/roles";
import type { PermissionOption as AdminPermissionOption, AdminRole } from "@/lib/types/roles";
import type { PermissionOption as HotelPermissionOption, HotelRole } from "@/lib/types/hotel-roles";

type Scope = "admin" | "hotel";
type PermissionOption = AdminPermissionOption | HotelPermissionOption;
type EditableRole = AdminRole | HotelRole;

const ACTION_PRIORITY = ["read", "create", "update", "delete", "export", "start", "stop"];
const ACTION_LABELS: Record<string, string> = {
  read: "View",
  create: "Add",
  update: "Edit",
  delete: "Delete",
  export: "Export",
  start: "Start",
  stop: "Stop"
};

const defaultForm = {
  name: "",
  display_name: "",
  description: ""
};

function humanize(value: string): string {
  return value
    .replace(/[_-]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function toResourceAction(permission: PermissionOption): { resource: string; action: string } {
  const fallback = permission.code.split(":");
  const resource = permission.resource || fallback[1] || "general";
  const action = permission.action || fallback[2] || "read";
  return { resource, action };
}

function sortActions(actions: string[]): string[] {
  const unique = Array.from(new Set(actions));
  unique.sort((a, b) => {
    const indexA = ACTION_PRIORITY.indexOf(a);
    const indexB = ACTION_PRIORITY.indexOf(b);

    if (indexA >= 0 && indexB >= 0) return indexA - indexB;
    if (indexA >= 0) return -1;
    if (indexB >= 0) return 1;
    return a.localeCompare(b);
  });
  return unique;
}

function getRoleApi(scope: Scope) {
  if (scope === "admin") {
    return {
      listPermissions: adminRolesApi.permissions,
      getRole: adminRolesApi.get,
      createRole: adminRolesApi.create,
      updateRole: adminRolesApi.update,
      listPath: "/admin/roles"
    };
  }

  return {
    listPermissions: hotelRolesApi.permissions,
    getRole: hotelRolesApi.get,
    createRole: hotelRolesApi.create,
    updateRole: hotelRolesApi.update,
    listPath: "/hotel/roles"
  };
}

export function RoleEditor({ scope, roleId }: { scope: Scope; roleId?: string }) {
  const router = useRouter();
  const api = useMemo(() => getRoleApi(scope), [scope]);

  const [form, setForm] = useState(defaultForm);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [permissions, setPermissions] = useState<PermissionOption[]>([]);
  const [role, setRole] = useState<EditableRole | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEdit = Boolean(roleId);
  const isSystemRole = Boolean(role?.is_system);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const permissionsData = await api.listPermissions();
      setPermissions(permissionsData);

      if (roleId) {
        const roleData = await api.getRole(roleId);
        setRole(roleData);
        setForm({
          name: roleData.name,
          display_name: roleData.display_name,
          description: roleData.description ?? ""
        });
        setSelectedPermissions(roleData.permissions);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load role form");
    } finally {
      setLoading(false);
    }
  }, [api, roleId]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const matrix = useMemo(() => {
    const resources = new Map<string, Map<string, PermissionOption>>();
    const actions: string[] = [];

    for (const permission of permissions) {
      if (permission.code.includes("*")) continue;
      const { resource, action } = toResourceAction(permission);
      if (resource === "*" || action === "*") continue;

      if (!resources.has(resource)) resources.set(resource, new Map());
      resources.get(resource)?.set(action, permission);
      actions.push(action);
    }

    const sortedActions = sortActions(actions);
    const rows = Array.from(resources.entries()).map(([resource, byAction]) => ({
      resource,
      permissions: sortedActions.map((action) => ({
        action,
        permission: byAction.get(action) ?? null
      }))
    }));

    return { actions: sortedActions, rows };
  }, [permissions]);

  const selectedSet = useMemo(() => new Set(selectedPermissions), [selectedPermissions]);

  const togglePermission = (code: string) => {
    if (isSystemRole) return;
    setSelectedPermissions((prev) =>
      prev.includes(code) ? prev.filter((item) => item !== code) : [...prev, code]
    );
  };

  const rowState = (resource: string) => {
    const row = matrix.rows.find((item) => item.resource === resource);
    if (!row) return { allSelected: false, codes: [] as string[] };

    const codes = row.permissions.filter((item) => item.permission).map((item) => item.permission!.code);
    const allSelected = codes.length > 0 && codes.every((code) => selectedSet.has(code));
    return { allSelected, codes };
  };

  const toggleRow = (resource: string) => {
    if (isSystemRole) return;

    setSelectedPermissions((prev) => {
      const prevSet = new Set(prev);
      const row = matrix.rows.find((item) => item.resource === resource);
      if (!row) return prev;

      const codes = row.permissions.filter((item) => item.permission).map((item) => item.permission!.code);
      const allSelected = codes.length > 0 && codes.every((code) => prevSet.has(code));

      if (allSelected) {
        codes.forEach((code) => prevSet.delete(code));
      } else {
        codes.forEach((code) => prevSet.add(code));
      }

      return Array.from(prevSet);
    });
  };

  const handleSave = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSystemRole) return;

    setSaving(true);
    setError(null);
    try {
      const payload = {
        name: form.name.trim(),
        display_name: form.display_name.trim(),
        description: form.description.trim() || undefined,
        permissions: selectedPermissions
      };

      if (isEdit && roleId) {
        await api.updateRole(roleId, payload);
      } else {
        await api.createRole(payload);
      }

      router.push(api.listPath);
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save role");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? "Edit Role" : "Create New Role"}
        description="Configure role details and permission matrix."
        rightSlot={
          <Link href={api.listPath} className="ui-btn ui-btn-secondary ui-btn-sm ui-anim">
            Back to Roles
          </Link>
        }
      />

      {loading ? (
        <InlineAlert tone="info" message="Loading role editor..." />
      ) : (
        <form className="space-y-6" onSubmit={handleSave}>
          <CrudFormCard title="Role Details">
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Role Name" required>
                <TextInput
                  value={form.name}
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                  placeholder={scope === "admin" ? "operations-manager" : "front-desk"}
                  required
                  disabled={isSystemRole}
                />
              </Field>
              <Field label="Display Name" required>
                <TextInput
                  value={form.display_name}
                  onChange={(event) => setForm((prev) => ({ ...prev, display_name: event.target.value }))}
                  placeholder={scope === "admin" ? "Operations Manager" : "Front Desk"}
                  required
                  disabled={isSystemRole}
                />
              </Field>
              <Field label="Description" className="md:col-span-2">
                <TextAreaInput
                  value={form.description}
                  onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
                  rows={3}
                  placeholder="Describe what this role is responsible for."
                  disabled={isSystemRole}
                />
              </Field>
            </div>

            {isSystemRole ? (
              <InlineAlert tone="warning" message="System roles are read-only and cannot be modified." className="mt-3" />
            ) : null}
          </CrudFormCard>

          <SectionCard
            title="Permission Matrix"
            actions={<Badge variant="neutral">{selectedPermissions.length} selected</Badge>}
          >
            {matrix.rows.length === 0 ? (
              <InlineAlert tone="info" message="No permissions available." />
            ) : (
              <ResponsiveTableContainer>
                <table className="ui-table min-w-[760px]">
                  <thead>
                    <tr>
                      <th className="pb-3">Module</th>
                      <th className="pb-3">Select All</th>
                      {matrix.actions.map((action) => (
                        <th key={action} className="pb-3">
                          {ACTION_LABELS[action] ?? humanize(action)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {matrix.rows.map((row) => {
                      const state = rowState(row.resource);

                      return (
                        <tr key={row.resource}>
                          <td className="py-3">
                            <p className="font-medium">{humanize(row.resource)}</p>
                            <p className="text-xs text-[color:var(--color-text-muted)]">{row.resource}</p>
                          </td>
                          <td className="py-3">
                            <input
                              type="checkbox"
                              checked={state.allSelected}
                              onChange={() => toggleRow(row.resource)}
                              disabled={isSystemRole || state.codes.length === 0}
                            />
                          </td>
                          {row.permissions.map((item) => (
                            <td key={`${row.resource}-${item.action}`} className="py-3">
                              {item.permission ? (
                                <input
                                  type="checkbox"
                                  checked={selectedSet.has(item.permission.code)}
                                  onChange={() => togglePermission(item.permission!.code)}
                                  disabled={isSystemRole}
                                  title={item.permission.code}
                                />
                              ) : (
                                <span className="text-[color:var(--color-text-muted)]">-</span>
                              )}
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </ResponsiveTableContainer>
            )}
          </SectionCard>

          {error ? <InlineAlert tone="error" message={error} /> : null}

          <div className="flex flex-wrap gap-3">
            <Button type="submit" variant="primary" disabled={saving || isSystemRole}>
              {saving ? "Saving..." : "Save Role"}
            </Button>
            <Link href={api.listPath} className="ui-btn ui-btn-secondary ui-btn-md ui-anim">
              Cancel
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}
