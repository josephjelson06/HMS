import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils/cn";

const textAreaInputVariants = cva("ui-textarea", {
  variants: {
    size: {
      sm: "text-xs",
      md: "",
      lg: "text-base"
    }
  },
  defaultVariants: {
    size: "md"
  }
});

export interface TextAreaInputProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement>,
    VariantProps<typeof textAreaInputVariants> {}

export function TextAreaInput({ className, size, ...props }: TextAreaInputProps) {
  return <textarea className={cn(textAreaInputVariants({ size }), className)} {...props} />;
}

export { textAreaInputVariants };
