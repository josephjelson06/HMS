import type { ReactNode } from "react";
import clsx from "clsx";

export function ResponsiveTableContainer({
  children,
  className
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={clsx("ui-table-wrap", className)}>{children}</div>;
}
