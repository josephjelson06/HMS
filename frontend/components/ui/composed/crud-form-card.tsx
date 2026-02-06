import type { ReactNode } from "react";

import { SectionCard } from "@/components/ui/composed/section-card";

export function CrudFormCard({
  title,
  children
}: {
  title: string;
  children: ReactNode;
}) {
  return <SectionCard title={title}>{children}</SectionCard>;
}
