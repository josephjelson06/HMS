import type { ReactNode } from "react";
import clsx from "clsx";

import { GlassCard } from "@/components/ui/glass-card";

export function SectionCard({
  title,
  actions,
  children,
  className
}: {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <GlassCard className={clsx("p-6 ui-reveal", className)}>
      {(title || actions) && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          {title ? <h3 className="text-lg">{title}</h3> : <span />}
          {actions}
        </div>
      )}
      <div className={clsx((title || actions) && "mt-4")}>{children}</div>
    </GlassCard>
  );
}
