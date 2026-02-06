import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils/cn";

const buttonVariants = cva("ui-btn ui-anim", {
  variants: {
    variant: {
      primary: "ui-btn-primary",
      secondary: "ui-btn-secondary",
      outline: "ui-btn-outline",
      danger: "ui-btn-danger",
      ghost: "ui-btn-ghost"
    },
    size: {
      sm: "ui-btn-sm",
      md: "ui-btn-md",
      lg: "ui-btn-lg"
    }
  },
  defaultVariants: {
    variant: "secondary",
    size: "md"
  }
});

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}

export { buttonVariants };
