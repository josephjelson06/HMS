"use client";

import { useCallback, useEffect, useState } from "react";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { DataTable } from "@/components/ui/composed/data-table";
import { DirectoryTableCard } from "@/components/ui/composed/directory-table-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { SectionCard } from "@/components/ui/composed/section-card";
import { GlassCard } from "@/components/ui/glass-card";
import { hotelBillingApi } from "@/lib/api/hotel/billing";
import type { BillingSummary } from "@/lib/types/billing";

export default function HotelBillingPage() {
  const [data, setData] = useState<BillingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBilling = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const summary = await hotelBillingApi.summary(20);
      setData(summary);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load billing summary");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchBilling();
  }, [fetchBilling]);

  return (
    <PermissionGuard
      permission="hotel:billing:read"
      fallback={
        <GlassCard className="p-6">
          <h2 className="text-2xl">Access denied</h2>
          <p className="mt-2 text-sm text-[color:var(--color-text-muted)]">
            You do not have permission to view billing.
          </p>
        </GlassCard>
      }
    >
      <div className="space-y-6">
        <PageHeader
          title="Subscription & Billing"
          description="Review plan details, subscription status, and invoices."
        />

        {error ? <InlineAlert tone="error" message={error} /> : null}

        {loading ? (
          <InlineAlert tone="info" message="Loading billing summary..." />
        ) : !data ? (
          <EmptyState description="Billing summary is not available." />
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <SectionCard title="Current Plan">
                {data.plan ? (
                  <div className="space-y-2 text-sm">
                    <p>
                      <span className="text-[color:var(--color-text-muted)]">Name:</span> {data.plan.name}
                    </p>
                    <p>
                      <span className="text-[color:var(--color-text-muted)]">Code:</span> {data.plan.code}
                    </p>
                    <p>
                      <span className="text-[color:var(--color-text-muted)]">Price:</span>{" "}
                      {(data.plan.price_cents / 100).toFixed(2)} {data.plan.currency} /{data.plan.billing_interval}
                    </p>
                    <p>
                      <span className="text-[color:var(--color-text-muted)]">Status:</span>{" "}
                      {data.plan.is_active ? "Active" : "Inactive"}
                    </p>
                  </div>
                ) : (
                  <InlineAlert tone="info" message="No plan assigned yet." />
                )}
              </SectionCard>

              <SectionCard title="Subscription">
                {data.subscription ? (
                  <div className="space-y-2 text-sm">
                    <p>
                      <span className="text-[color:var(--color-text-muted)]">Status:</span> {data.subscription.status}
                    </p>
                    <p>
                      <span className="text-[color:var(--color-text-muted)]">Period Start:</span>{" "}
                      {data.subscription.current_period_start
                        ? new Date(data.subscription.current_period_start).toLocaleDateString()
                        : "-"}
                    </p>
                    <p>
                      <span className="text-[color:var(--color-text-muted)]">Period End:</span>{" "}
                      {data.subscription.current_period_end
                        ? new Date(data.subscription.current_period_end).toLocaleDateString()
                        : "-"}
                    </p>
                    <p>
                      <span className="text-[color:var(--color-text-muted)]">Cancel At:</span>{" "}
                      {data.subscription.cancel_at
                        ? new Date(data.subscription.cancel_at).toLocaleDateString()
                        : "-"}
                    </p>
                  </div>
                ) : (
                  <InlineAlert tone="info" message="No subscription data available." />
                )}
              </SectionCard>
            </div>

            {data.invoices.length === 0 ? (
              <EmptyState description="No invoices yet." />
            ) : (
              <DirectoryTableCard
                title="Invoices"
                table={
                  <DataTable
                    columns={[
                      {
                        key: "invoice",
                        header: "Invoice",
                        cellClassName: "font-medium",
                        render: (invoice) => invoice.invoice_number
                      },
                      { key: "status", header: "Status", render: (invoice) => invoice.status },
                      {
                        key: "amount",
                        header: "Amount",
                        render: (invoice) => `${(invoice.amount_cents / 100).toFixed(2)} ${invoice.currency}`
                      },
                      {
                        key: "issued",
                        header: "Issued",
                        render: (invoice) =>
                          invoice.issued_at ? new Date(invoice.issued_at).toLocaleDateString() : "-"
                      },
                      {
                        key: "due",
                        header: "Due",
                        render: (invoice) =>
                          invoice.due_at ? new Date(invoice.due_at).toLocaleDateString() : "-"
                      }
                    ]}
                    rows={data.invoices}
                    rowKey={(invoice) => invoice.id}
                  />
                }
              />
            )}
          </>
        )}
      </div>
    </PermissionGuard>
  );
}
