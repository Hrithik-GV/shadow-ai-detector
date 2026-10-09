import React from 'react';
import { EmptyState } from './EmptyState';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string | number;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  emptyTitle = 'No telemetry records found',
  emptyDescription = 'No data available from the detection engine yet. Active records will appear here.',
  className = '',
}: TableProps<T>) {
  if (data.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} className={className} />;
  }

  return (
    <div
      className={`border-2 border-[#333330] bg-[#171716] shadow-[4px_4px_0_#000000] overflow-x-auto ${className}`}
    >
      <table className="w-full border-collapse font-mono text-xs text-left">
        <thead>
          <tr className="bg-[#181818] border-b-2 border-[#333330]">
            {columns.map((col) => (
              <th
                key={col.key}
                style={{ width: col.width }}
                className={`py-3 px-4 font-mono font-bold uppercase tracking-wider text-[#FFCC00] ${
                  col.align === 'center'
                    ? 'text-center'
                    : col.align === 'right'
                    ? 'text-right'
                    : 'text-left'
                }`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#333330]">
          {data.map((item) => (
            <tr
              key={keyExtractor(item)}
              className="hover:bg-[#1E1E1C] transition-colors duration-100"
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`py-3 px-4 text-[#F4F4F0] ${
                    col.align === 'center'
                      ? 'text-center'
                      : col.align === 'right'
                      ? 'text-right'
                      : 'text-left'
                  }`}
                >
                  {col.render
                    ? col.render(item)
                    : (item as Record<string, unknown>)[col.key] !== undefined
                    ? String((item as Record<string, unknown>)[col.key])
                    : '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
