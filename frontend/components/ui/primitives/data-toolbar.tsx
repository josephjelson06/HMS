"use client";

import { Search } from "lucide-react";

import { Button } from "@/components/ui/primitives/button";
import { SelectInput } from "@/components/ui/primitives/select-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { cn } from "@/lib/utils/cn";

export interface SortOption {
  value: string;
  label: string;
}

export interface SortState<T = string> {
  field: T;
  direction: "asc" | "desc";
}

export interface FilterFieldConfig {
  key: string;
  label: string;
}

export interface FilterPanelProps {
  onApply?: () => void;
  onReset?: () => void;
}

export interface DataToolbarProps {
  search?: string;
  onSearchChange?: (value: string) => void;
  onSearchSubmit?: () => void;
  searchPlaceholder?: string;
  sortValue?: string;
  sortOptions?: SortOption[];
  onSortChange?: (value: string) => void;
  filtersSlot?: React.ReactNode;
  actionsSlot?: React.ReactNode;
  className?: string;
}

export function DataToolbar({
  search,
  onSearchChange,
  onSearchSubmit,
  searchPlaceholder = "Search...",
  sortValue,
  sortOptions = [],
  onSortChange,
  filtersSlot,
  actionsSlot,
  className
}: DataToolbarProps) {
  return (
    <div className={cn("flex flex-wrap items-end gap-3", className)}>
      {typeof search === "string" ? (
        <div className="min-w-[220px] flex-1">
          <label className="mb-1.5 block text-xs text-[color:var(--color-text-muted)]">Search</label>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[color:var(--color-text-muted)]" />
              <TextInput
                className="pl-9"
                value={search}
                onChange={(event) => onSearchChange?.(event.target.value)}
                placeholder={searchPlaceholder}
              />
            </div>
            {onSearchSubmit ? (
              <Button variant="secondary" onClick={onSearchSubmit}>
                Apply
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}

      {sortOptions.length > 0 && sortValue !== undefined ? (
        <div className="min-w-[180px]">
          <label className="mb-1.5 block text-xs text-[color:var(--color-text-muted)]">Sort</label>
          <SelectInput value={sortValue} onChange={(event) => onSortChange?.(event.target.value)}>
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </SelectInput>
        </div>
      ) : null}

      {filtersSlot ? <div className="flex-1 min-w-[220px]">{filtersSlot}</div> : null}
      {actionsSlot ? <div className="ml-auto flex flex-wrap items-center gap-2">{actionsSlot}</div> : null}
    </div>
  );
}
