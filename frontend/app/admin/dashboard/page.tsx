"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { SectionCard } from "@/components/ui/composed/section-card";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/primitives/badge";
import { Button } from "@/components/ui/primitives/button";
import { adminDashboardApi } from "@/lib/api/admin/dashboard";
import type { AdminDashboardSummary } from "@/lib/types/dashboard";

const formatCurrency = (valueCents: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(valueCents / 100);

export default function AdminDashboard() {
  const [summary, setSummary] = useState<AdminDashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminDashboardApi.summary();
      setSummary(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard summary");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSummary();
  }, [fetchSummary]);

  const cards = useMemo(() => {
    if (!summary) return [];
    return [
      { label: "Hotels", value: summary.total_hotels.toLocaleString() },
      { label: "Active Hotels", value: summary.active_hotels.toLocaleString() },
      { label: "Active Subscriptions", value: summary.active_subscriptions.toLocaleString() },
      { label: "Monthly Paid Revenue", value: formatCurrency(summary.monthly_revenue_cents) },
      { label: "Outstanding Balance", value: formatCurrency(summary.outstanding_balance_cents) },
      { label: "Open Helpdesk Tickets", value: summary.open_helpdesk_tickets.toLocaleString() },
      { label: "New Hotels (30d)", value: summary.new_hotels_last_30_days.toLocaleString() }
    ];
  }, [summary]);

  const cardsToRender = useMemo(() => (loading ? Array.from({ length: 4 }, () => null) : cards), [cards, loading]);

  return (
    <PermissionGuard
      permission="admin:dashboard:read"
      fallback={
        <GlassCard className="p-6">
          <h2 className="text-2xl">Access denied</h2>
          <p className="mt-2 text-sm text-[color:var(--color-text-muted)]">
            You do not have permission to view dashboard metrics.
          </p>
        </GlassCard>
      }
    >
      <div className="space-y-6">
        <PageHeader
          title="Platform Dashboard"
          description="Real-time top-line signals for tenant growth, billing, and support."
          rightSlot={
            <Button variant="secondary" onClick={() => void fetchSummary()} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh"}
            </Button>
          }
        />

        {error ? <InlineAlert tone="error" message={error} /> : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {cardsToRender.map((card, index) => (
            <SectionCard key={card?.label ?? index}>
              {card ? (
                <>
                  <p className="text-xs uppercase tracking-wide text-[color:var(--color-text-muted)]">{card.label}</p>
                  <p className="mt-2 text-2xl font-semibold">{card.value}</p>
                </>
              ) : (
                <div className="h-12 animate-pulse rounded bg-white/10" />
              )}
            </SectionCard>
          ))}
        </div>

        {!summary || summary.recent_hotels.length === 0 ? (
          <EmptyState description="No recent hotels yet." />
        ) : (
          <SectionCard title="Recent Hotels">
            <div className="space-y-3">
              {summary.recent_hotels.map((hotel) => (
                <div
                  key={hotel.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 px-4 py-3"
                >
                  <div>
                    <p className="font-medium">{hotel.name}</p>
                    <p className="text-xs text-[color:var(--color-text-muted)]">
                      Created {hotel.created_at ? new Date(hotel.created_at).toLocaleString() : "N/A"}
                    </p>
                  </div>
                  <Badge className="capitalize">{hotel.status}</Badge>
                </div>
              ))}
            </div>
          </SectionCard>
        )}
      </div>
    </PermissionGuard>
  );
}
