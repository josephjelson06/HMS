import { SectionCard } from "@/components/ui/composed/section-card";

export interface DetailPlaceholderProps {
  title: string;
  message?: string;
}

export function DetailPlaceholder({
  title,
  message = "Detail view will be expanded in the next iteration."
}: DetailPlaceholderProps) {
  return (
    <SectionCard title={title}>
      <p className="text-sm text-[color:var(--color-text-muted)]">{message}</p>
    </SectionCard>
  );
}
