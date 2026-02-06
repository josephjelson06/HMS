"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/primitives/button";
import { cn } from "@/lib/utils/cn";

export interface PaginationState {
  page: number;
  limit: number;
  total: number;
}

export interface PaginationProps extends PaginationState {
  onPageChange: (page: number) => void;
  className?: string;
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

export function Pagination({ page, limit, total, onPageChange, className }: PaginationProps) {
  const safeLimit = Math.max(1, limit);
  const totalPages = Math.max(1, Math.ceil(total / safeLimit));
  const currentPage = clamp(page, 1, totalPages);
  const start = total === 0 ? 0 : (currentPage - 1) * safeLimit + 1;
  const end = total === 0 ? 0 : Math.min(total, currentPage * safeLimit);

  return (
    <div className={cn("flex flex-wrap items-center justify-between gap-3", className)}>
      <p className="text-xs text-[color:var(--color-text-muted)]">
        Showing {start}-{end} of {total}
      </p>
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
        >
          <ChevronLeft className="mr-1 size-4" />
          Prev
        </Button>
        <span className="text-xs text-[color:var(--color-text-muted)]">
          Page {currentPage} / {totalPages}
        </span>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
        >
          Next
          <ChevronRight className="ml-1 size-4" />
        </Button>
      </div>
    </div>
  );
}
