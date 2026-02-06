import { GlassCard } from "@/components/ui/glass-card";

export interface EmptyStateProps {
  title?: string;
  description: string;
}

export function EmptyState({ title = "Nothing here yet", description }: EmptyStateProps) {
  return (
    <GlassCard className="p-6">
      <h3 className="text-lg">{title}</h3>
      <p className="mt-2 text-sm text-[color:var(--color-text-muted)]">{description}</p>
    </GlassCard>
  );
}
