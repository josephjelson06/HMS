import type { ReactNode } from "react";
import clsx from "clsx";

export function TableActionCell({
  children,
  className
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={clsx("flex flex-wrap gap-2", className)}>{children}</div>;
}
