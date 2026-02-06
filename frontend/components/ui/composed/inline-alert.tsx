import clsx from "clsx";

export interface InlineAlertProps {
  tone?: "error" | "info" | "success" | "warning";
  message: string;
  className?: string;
}

export function InlineAlert({ tone = "info", message, className }: InlineAlertProps) {
  return <p className={clsx("ui-inline-alert", `ui-inline-alert-${tone}`, className)}>{message}</p>;
}
