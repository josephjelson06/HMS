import type { ReactNode } from "react";

import { cn } from "@/lib/utils/cn";

export function StickyActionBar({
  children,
  className
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "sticky bottom-4 z-20 flex flex-wrap items-center justify-end gap-2 rounded-xl border border-white/10 bg-[color:var(--glass-strong)] px-3 py-2 backdrop-blur-xl",
        className
      )}
    >
      {children}
    </div>
  );
}
