import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils/cn";

const iconButtonVariants = cva("ui-btn ui-icon-btn ui-anim", {
  variants: {
    variant: {
      outline: "ui-btn-outline",
      ghost: "ui-btn-ghost",
      secondary: "ui-btn-secondary"
    }
  },
  defaultVariants: {
    variant: "outline"
  }
});

export interface IconButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof iconButtonVariants> {
  label: string;
}

export function IconButton({ className, label, variant, ...props }: IconButtonProps) {
  return (
    <button
      aria-label={label}
      title={label}
      className={cn(iconButtonVariants({ variant }), className)}
      {...props}
    />
  );
}
