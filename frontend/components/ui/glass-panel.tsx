import type { ReactNode } from "react";
import clsx from "clsx";

export function GlassPanel({
  children,
  className
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={clsx("glass-panel", className)}>{children}</div>;
}
