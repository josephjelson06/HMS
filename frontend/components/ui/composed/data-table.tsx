import type { ReactNode } from "react";
import clsx from "clsx";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  headerClassName?: string;
  cellClassName?: string;
  render: (row: T, rowIndex: number) => ReactNode;
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T, rowIndex: number) => string;
  emptyFallback?: ReactNode;
  className?: string;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyFallback = null,
  className
}: DataTableProps<T>) {
  if (rows.length === 0) {
    return <>{emptyFallback}</>;
  }

  return (
    <table className={clsx("ui-table", className)}>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} className={clsx("pb-3", column.headerClassName)}>
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, rowIndex) => (
          <tr key={rowKey(row, rowIndex)}>
            {columns.map((column) => (
              <td key={column.key} className={clsx("py-3", column.cellClassName)}>
                {column.render(row, rowIndex)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
