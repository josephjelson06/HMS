import type { ReactNode } from "react";
import { ArrowDownUp, ArrowDown, ArrowUp } from "lucide-react";

import { cn } from "@/lib/utils/cn";

export interface DataGridColumn<T> {
  key: string;
  header: string;
  sortable?: boolean;
  headerClassName?: string;
  cellClassName?: string;
  render: (row: T, rowIndex: number) => ReactNode;
}

export interface DataGridSort {
  key: string;
  direction: "asc" | "desc";
}

export interface DataGridProps<T> {
  columns: DataGridColumn<T>[];
  rows: T[];
  rowKey: (row: T, rowIndex: number) => string;
  sort?: DataGridSort | null;
  onSortChange?: (next: DataGridSort) => void;
  loading?: boolean;
  emptyFallback?: ReactNode;
  loadingFallback?: ReactNode;
  className?: string;
}

function SortIcon({ active, direction }: { active: boolean; direction?: "asc" | "desc" }) {
  if (!active) return <ArrowDownUp className="size-3.5 text-[color:var(--color-text-muted)]" />;
  if (direction === "asc") return <ArrowUp className="size-3.5" />;
  return <ArrowDown className="size-3.5" />;
}

export function DataGrid<T>({
  columns,
  rows,
  rowKey,
  sort,
  onSortChange,
  loading = false,
  emptyFallback = null,
  loadingFallback = null,
  className
}: DataGridProps<T>) {
  if (loading) return <>{loadingFallback}</>;
  if (rows.length === 0) return <>{emptyFallback}</>;

  return (
    <table className={cn("ui-table", className)}>
      <thead>
        <tr>
          {columns.map((column) => {
            const active = sort?.key === column.key;
            const clickable = Boolean(onSortChange && column.sortable);
            return (
              <th key={column.key} className={cn("pb-3", column.headerClassName)}>
                {clickable ? (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 text-left ui-anim"
                    onClick={() =>
                      onSortChange({
                        key: column.key,
                        direction: active && sort?.direction === "asc" ? "desc" : "asc"
                      })
                    }
                  >
                    {column.header}
                    <SortIcon active={active} direction={sort?.direction} />
                  </button>
                ) : (
                  column.header
                )}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIndex) => (
          <tr key={rowKey(row, rowIndex)}>
            {columns.map((column) => (
              <td key={column.key} className={cn("py-3", column.cellClassName)}>
                {column.render(row, rowIndex)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
