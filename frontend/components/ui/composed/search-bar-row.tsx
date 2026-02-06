import type { ReactNode } from "react";

export function SearchBarRow({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap gap-3">{children}</div>;
}
