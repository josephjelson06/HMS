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
import { hotelRoomsApi } from "@/lib/api/hotel/rooms";
import type { Room } from "@/lib/types/rooms";

const defaultForm = {
  number: "",
  room_type: "",
  floor: "",
  status: "available",
  capacity: "",
  rate_cents: "",
  currency: "USD",
  description: ""
};

export default function HotelRoomsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Room | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Room | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchRooms = useCallback(async (nextPage = page, nextSearch = search) => {
    setLoading(true);
    setError(null);
    try {
      const data = await hotelRoomsApi.list({ page: nextPage, limit, search: nextSearch || undefined });
      setRooms(data.items);
      setPage(data.pagination.page);
      setTotal(data.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load rooms");
    } finally {
      setLoading(false);
    }
  }, [limit, page, search]);

  useEffect(() => {
    void fetchRooms(page, search);
  }, [fetchRooms, page, search]);

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
      number: form.number,
      room_type: form.room_type,
      floor: form.floor || undefined,
      status: form.status || undefined,
      capacity: form.capacity ? Number(form.capacity) : undefined,
      rate_cents: form.rate_cents ? Number(form.rate_cents) : undefined,
      currency: form.currency || undefined,
      description: form.description || undefined
    }),
    [form]
  );

  const updatePayload = useMemo(
    () => ({
      number: form.number || undefined,
      room_type: form.room_type || undefined,
      floor: form.floor || undefined,
      status: form.status || undefined,
      capacity: form.capacity ? Number(form.capacity) : undefined,
      rate_cents: form.rate_cents ? Number(form.rate_cents) : undefined,
      currency: form.currency || undefined,
      description: form.description || undefined
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await hotelRoomsApi.update(editing.id, updatePayload);
        toast.success("Room updated");
      } else {
        await hotelRoomsApi.create(createPayload);
        toast.success("Room created");
      }
      setFormOpen(false);
      resetForm();
      await fetchRooms(page, search);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save room";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (room: Room) => {
    setEditing(room);
    setForm({
      number: room.number,
      room_type: room.room_type,
      floor: room.floor ?? "",
      status: room.status,
      capacity: room.capacity ? String(room.capacity) : "",
      rate_cents: room.rate_cents ? String(room.rate_cents) : "",
      currency: room.currency,
      description: room.description ?? ""
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await hotelRoomsApi.remove(pendingDelete.id);
      toast.success("Room deleted");
      setPendingDelete(null);
      await fetchRooms(page, search);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete room";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="hotel:rooms:read"
      fallback={<AccessDeniedState message="You do not have permission to view room management." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Room Management"
          description="Track room inventory, availability, and pricing."
          count={total}
          countLabel="Rooms"
          rightSlot={
            <PermissionGuard permission="hotel:rooms:create">
              <Button variant="primary" onClick={openCreate}>
                Add Room
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Room Directory"
          table={
            <>
              <DataToolbar
                search={search}
                onSearchChange={(value) => setSearch(value)}
                onSearchSubmit={() => {
                  setPage(1);
                  void fetchRooms(1, search);
                }}
                searchPlaceholder="Search by number or type"
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchRooms(page, search)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading rooms..." className="mt-3" />
              ) : rooms.length === 0 ? (
                <EmptyState description="No rooms added yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      { key: "number", header: "Number", cellClassName: "font-medium", render: (room) => room.number },
                      {
                        key: "type",
                        header: "Type",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (room) => room.room_type
                      },
                      { key: "status", header: "Status", render: (room) => room.status },
                      { key: "capacity", header: "Capacity", render: (room) => room.capacity ?? "-" },
                      {
                        key: "rate",
                        header: "Rate",
                        render: (room) => `${room.rate_cents ? (room.rate_cents / 100).toFixed(2) : "-"} ${room.currency}`
                      },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (room) => (
                          <TableActionCell>
                            <PermissionGuard permission="hotel:rooms:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(room)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="hotel:rooms:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(room)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={rooms}
                    rowKey={(room) => room.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "hotel:rooms:update" : "hotel:rooms:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Room" : "Add Room"}
          description="Maintain room inventory metadata and pricing."
          maxWidthClassName="max-w-5xl"
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Room Number" required>
              <TextInput value={form.number} onChange={(event) => handleChange("number", event.target.value)} placeholder="101" />
            </Field>
            <Field label="Room Type" required>
              <TextInput value={form.room_type} onChange={(event) => handleChange("room_type", event.target.value)} placeholder="Deluxe" />
            </Field>
            <Field label="Floor">
              <TextInput value={form.floor} onChange={(event) => handleChange("floor", event.target.value)} placeholder="1" />
            </Field>
            <Field label="Status">
              <TextInput value={form.status} onChange={(event) => handleChange("status", event.target.value)} placeholder="available" />
            </Field>
            <Field label="Capacity">
              <TextInput value={form.capacity} onChange={(event) => handleChange("capacity", event.target.value)} placeholder="2" />
            </Field>
            <Field label="Rate (cents)">
              <TextInput value={form.rate_cents} onChange={(event) => handleChange("rate_cents", event.target.value)} placeholder="12900" />
            </Field>
            <Field label="Currency">
              <TextInput value={form.currency} onChange={(event) => handleChange("currency", event.target.value)} placeholder="USD" />
            </Field>
            <Field label="Description" className="md:col-span-2">
              <TextAreaInput value={form.description} onChange={(event) => handleChange("description", event.target.value)} rows={3} />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Room"}
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
        title="Delete room"
        description={pendingDelete ? `Delete room ${pendingDelete.number}? This action cannot be undone.` : "Delete room?"}
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
