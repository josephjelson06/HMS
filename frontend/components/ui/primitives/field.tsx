import type { ReactNode } from "react";

import { cn } from "@/lib/utils/cn";

export interface FieldProps {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string;
  className?: string;
  children: ReactNode;
}

export function Field({ label, required, hint, error, className, children }: FieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <label className="text-sm font-medium">
        {label}
        {required && <span className="ml-1 text-[color:var(--color-accent)]">*</span>}
      </label>
      {children}
      {error ? (
        <p className="text-xs text-red-400">{error}</p>
      ) : hint ? (
        <p className="text-xs text-[color:var(--color-text-muted)]">{hint}</p>
      ) : null}
    </div>
  );
}
