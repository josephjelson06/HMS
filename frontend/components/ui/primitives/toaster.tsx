"use client";

import { Toaster as Sonner } from "sonner";

export interface ToastAction {
  label: string;
  onClick: () => void;
}

export interface ToastPayload {
  title: string;
  description?: string;
  action?: ToastAction;
}

export function Toaster() {
  return (
    <Sonner
      richColors
      closeButton
      position="top-right"
      toastOptions={{
        classNames: {
          toast:
            "border border-[color:var(--color-border-subtle)] !bg-[color:var(--glass-strong)] !text-[color:var(--color-text-primary)] backdrop-blur-xl",
          description: "!text-[color:var(--color-text-muted)]",
          actionButton: "!bg-[color:var(--color-accent)] !text-black",
          cancelButton: "!bg-white/10 !text-[color:var(--color-text-primary)]"
        }
      }}
    />
  );
}
