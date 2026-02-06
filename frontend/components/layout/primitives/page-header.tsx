import type { ReactNode } from "react";
import clsx from "clsx";

import { Badge } from "@/components/ui/primitives/badge";

export interface PageHeaderProps {
  title: string;
  description?: string;
  rightSlot?: ReactNode;
  count?: number;
  countLabel?: string;
  className?: string;
}

export function PageHeader({
  title,
  description,
  rightSlot,
  count,
  countLabel,
  className
}: PageHeaderProps) {
  return (
    <div className={clsx("ui-page-header", className)}>
      <div>
        <h2 className="ui-page-title">{title}</h2>
        {description ? <p className="ui-page-subtitle">{description}</p> : null}
      </div>
      <div className="flex items-center gap-3">
        {typeof count === "number" ? (
          <Badge variant="accent">
            {count}
            {countLabel ? ` ${countLabel}` : ""}
          </Badge>
        ) : null}
        {rightSlot}
      </div>
    </div>
  );
}
