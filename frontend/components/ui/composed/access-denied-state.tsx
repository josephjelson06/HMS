import type { ReactNode } from "react";

import { SectionCard } from "@/components/ui/composed/section-card";

export interface AccessDeniedStateProps {
  message: string;
  title?: string;
  className?: string;
  children?: ReactNode;
}

export function AccessDeniedState({
  message,
  title = "Access denied",
  className,
  children
}: AccessDeniedStateProps) {
  return (
    <SectionCard title={title} className={className}>
      <p className="text-sm text-[color:var(--color-text-muted)]">{message}</p>
      {children ? <div className="mt-4">{children}</div> : null}
    </SectionCard>
  );
}
