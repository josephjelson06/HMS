import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils/cn";

const selectInputVariants = cva("ui-select", {
  variants: {
    size: {
      sm: "py-2 text-xs",
      md: "",
      lg: "py-3.5 text-base"
    }
  },
  defaultVariants: {
    size: "md"
  }
});

export interface SelectInputProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "size">,
    VariantProps<typeof selectInputVariants> {}

export function SelectInput({ className, size, children, ...props }: SelectInputProps) {
  return (
    <select className={cn(selectInputVariants({ size }), className)} {...props}>
      {children}
    </select>
  );
}

export { selectInputVariants };
