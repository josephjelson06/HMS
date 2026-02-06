import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils/cn";

const textInputVariants = cva("ui-input", {
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

export interface TextInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">,
    VariantProps<typeof textInputVariants> {}

export function TextInput({ className, size, ...props }: TextInputProps) {
  return <input className={cn(textInputVariants({ size }), className)} {...props} />;
}

export { textInputVariants };
