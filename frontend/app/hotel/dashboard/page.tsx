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
import { hotelDashboardApi } from "@/lib/api/hotel/dashboard";
import type { HotelDashboardSummary } from "@/lib/types/dashboard";

const formatCurrency = (valueCents: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(valueCents / 100);

export default function HotelDashboard() {
  const [summary, setSummary] = useState<HotelDashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await hotelDashboardApi.summary();
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
      { label: "Total Guests", value: summary.total_guests.toLocaleString() },
      { label: "Active Guests", value: summary.active_guests.toLocaleString() },
      { label: "Total Rooms", value: summary.total_rooms.toLocaleString() },
      { label: "Occupied Rooms", value: summary.occupied_rooms.toLocaleString() },
      { label: "Occupancy", value: `${summary.occupancy_rate}%` },
      { label: "Open Incidents", value: summary.open_incidents.toLocaleString() },
      { label: "Open Support Tickets", value: summary.open_helpdesk_tickets.toLocaleString() },
      { label: "Active Kiosks", value: summary.active_kiosks.toLocaleString() },
      { label: "Outstanding Balance", value: formatCurrency(summary.outstanding_balance_cents) }
    ];
  }, [summary]);

  const cardsToRender = useMemo(() => (loading ? Array.from({ length: 6 }, () => null) : cards), [cards, loading]);

  return (
    <PermissionGuard
      permission="hotel:dashboard:read"
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
          title="Hotel Dashboard"
          description="Operational overview across guests, occupancy, incidents, and billing."
          rightSlot={
            <Button variant="secondary" onClick={() => void fetchSummary()} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh"}
            </Button>
          }
        />

        {error ? <InlineAlert tone="error" message={error} /> : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
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

        {!summary || summary.recent_incidents.length === 0 ? (
          <EmptyState description="No recent incidents." />
        ) : (
          <SectionCard title="Recent Incidents">
            <div className="space-y-3">
              {summary.recent_incidents.map((incident) => (
                <div
                  key={incident.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 px-4 py-3"
                >
                  <div>
                    <p className="font-medium">{incident.title}</p>
                    <p className="text-xs text-[color:var(--color-text-muted)]">
                      {incident.occurred_at ? new Date(incident.occurred_at).toLocaleString() : "No occurred date"}
                    </p>
                  </div>
                  <div className="flex gap-2 text-xs">
                    <Badge className="capitalize">{incident.status}</Badge>
                    <Badge variant="warning" className="capitalize">
                      {incident.severity}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        )}
      </div>
    </PermissionGuard>
  );
}
