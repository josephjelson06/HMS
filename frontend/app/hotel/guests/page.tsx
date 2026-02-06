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
import { TextAreaInput } from "@/components/ui/primitives/textarea-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { hotelGuestsApi } from "@/lib/api/hotel/guests";
import type { Guest } from "@/lib/types/guests";

const defaultForm = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  status: "active",
  check_in_at: "",
  check_out_at: "",
  notes: ""
};

const toIso = (value: string) => {
  if (!value) return undefined;
  const date = new Date(value);
  return isNaN(date.getTime()) ? undefined : date.toISOString();
};

const toDateInput = (value?: string | null) => {
  if (!value) return "";
  return value.slice(0, 10);
};

export default function HotelGuestsPage() {
  const [guests, setGuests] = useState<Guest[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Guest | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Guest | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchGuests = useCallback(async (nextPage = page, nextSearch = search) => {
    setLoading(true);
    setError(null);
    try {
      const data = await hotelGuestsApi.list({
        page: nextPage,
        limit,
        search: nextSearch || undefined
      });
      setGuests(data.items);
      setPage(data.pagination.page);
      setTotal(data.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load guests");
    } finally {
      setLoading(false);
    }
  }, [limit, page, search]);

  useEffect(() => {
    void fetchGuests(page, search);
  }, [fetchGuests, page, search]);

  const handleChange = (field: keyof typeof defaultForm, value: string) => {
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

  const createPayload = useMemo(
    () => ({
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email || undefined,
      phone: form.phone || undefined,
      status: form.status || undefined,
      check_in_at: toIso(form.check_in_at),
      check_out_at: toIso(form.check_out_at),
      notes: form.notes || undefined
    }),
    [form]
  );

  const updatePayload = useMemo(
    () => ({
      first_name: form.first_name || undefined,
      last_name: form.last_name || undefined,
      email: form.email || undefined,
      phone: form.phone || undefined,
      status: form.status || undefined,
      check_in_at: toIso(form.check_in_at),
      check_out_at: toIso(form.check_out_at),
      notes: form.notes || undefined
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await hotelGuestsApi.update(editing.id, updatePayload);
        toast.success("Guest updated");
      } else {
        await hotelGuestsApi.create(createPayload);
        toast.success("Guest created");
      }
      setFormOpen(false);
      resetForm();
      await fetchGuests(page, search);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save guest";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (guest: Guest) => {
    setEditing(guest);
    setForm({
      first_name: guest.first_name,
      last_name: guest.last_name,
      email: guest.email ?? "",
      phone: guest.phone ?? "",
      status: guest.status,
      check_in_at: toDateInput(guest.check_in_at),
      check_out_at: toDateInput(guest.check_out_at),
      notes: guest.notes ?? ""
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await hotelGuestsApi.remove(pendingDelete.id);
      toast.success("Guest deleted");
      setPendingDelete(null);
      await fetchGuests(page, search);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete guest";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="hotel:guests:read"
      fallback={<AccessDeniedState message="You do not have permission to view the guest registry." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Guest Registry"
          description="Track active and upcoming guests for your property."
          count={total}
          countLabel="Guests"
          rightSlot={
            <PermissionGuard permission="hotel:guests:create">
              <Button variant="primary" onClick={openCreate}>
                Add Guest
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Guest Directory"
          table={
            <>
              <DataToolbar
                search={search}
                onSearchChange={(value) => setSearch(value)}
                onSearchSubmit={() => {
                  setPage(1);
                  void fetchGuests(1, search);
                }}
                searchPlaceholder="Search by name or email"
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchGuests(page, search)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading guests..." className="mt-3" />
              ) : guests.length === 0 ? (
                <EmptyState description="No guests added yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      {
                        key: "guest",
                        header: "Guest",
                        cellClassName: "font-medium",
                        render: (guest) => `${guest.first_name} ${guest.last_name}`
                      },
                      {
                        key: "email",
                        header: "Email",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (guest) => guest.email ?? "-"
                      },
                      { key: "status", header: "Status", render: (guest) => guest.status },
                      {
                        key: "check_in",
                        header: "Check In",
                        render: (guest) => (guest.check_in_at ? new Date(guest.check_in_at).toLocaleDateString() : "-")
                      },
                      {
                        key: "check_out",
                        header: "Check Out",
                        render: (guest) => (guest.check_out_at ? new Date(guest.check_out_at).toLocaleDateString() : "-")
                      },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (guest) => (
                          <TableActionCell>
                            <PermissionGuard permission="hotel:guests:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(guest)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="hotel:guests:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(guest)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={guests}
                    rowKey={(guest) => guest.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "hotel:guests:update" : "hotel:guests:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Guest" : "Add Guest"}
          description="Manage guest profile, stay dates, and contact details."
          maxWidthClassName="max-w-5xl"
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="First Name" required>
              <TextInput value={form.first_name} onChange={(event) => handleChange("first_name", event.target.value)} />
            </Field>
            <Field label="Last Name" required>
              <TextInput value={form.last_name} onChange={(event) => handleChange("last_name", event.target.value)} />
            </Field>
            <Field label="Email">
              <TextInput
                value={form.email}
                onChange={(event) => handleChange("email", event.target.value)}
                placeholder="guest@example.com"
              />
            </Field>
            <Field label="Phone">
              <TextInput
                value={form.phone}
                onChange={(event) => handleChange("phone", event.target.value)}
                placeholder="+1 555 123 4567"
              />
            </Field>
            <Field label="Status">
              <TextInput value={form.status} onChange={(event) => handleChange("status", event.target.value)} />
            </Field>
            <Field label="Check In">
              <TextInput type="date" value={form.check_in_at} onChange={(event) => handleChange("check_in_at", event.target.value)} />
            </Field>
            <Field label="Check Out">
              <TextInput type="date" value={form.check_out_at} onChange={(event) => handleChange("check_out_at", event.target.value)} />
            </Field>
            <Field label="Notes" className="md:col-span-2">
              <TextAreaInput value={form.notes} onChange={(event) => handleChange("notes", event.target.value)} rows={3} />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Guest"}
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
        title="Delete guest"
        description={pendingDelete ? `Delete ${pendingDelete.first_name} ${pendingDelete.last_name}? This action cannot be undone.` : "Delete guest?"}
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
