import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils/cn";

const badgeVariants = cva("badge", {
  variants: {
    variant: {
      accent: "badge-accent",
      neutral: "badge-neutral",
      success: "badge-success",
      warning: "badge-warning"
    }
  },
  defaultVariants: {
    variant: "accent"
  }
});

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { badgeVariants };
