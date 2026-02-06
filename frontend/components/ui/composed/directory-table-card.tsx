import type { ReactNode } from "react";

import { ResponsiveTableContainer } from "@/components/ui/composed/responsive-table-container";
import { SectionCard } from "@/components/ui/composed/section-card";

export function DirectoryTableCard({
  title,
  table,
  footer
}: {
  title: string;
  table: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <SectionCard title={title}>
      <ResponsiveTableContainer>{table}</ResponsiveTableContainer>
      {footer ? <div className="mt-3">{footer}</div> : null}
    </SectionCard>
  );
}
