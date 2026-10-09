import React from 'react';
import type { ProviderDistributionItem } from '../../types';

export interface ProviderDistributionBarsProps {
  data?: ProviderDistributionItem[] | Record<string, number>;
}

export const ProviderDistributionBars: React.FC<ProviderDistributionBarsProps> = ({ data }) => {
  if (!data) return null;

  // Normalize array or record into standard array
  const items: ProviderDistributionItem[] = Array.isArray(data)
    ? data
    : Object.entries(data).map(([provider, count]) => ({ provider, count }));

  if (items.length === 0) return null;

  const total = items.reduce((acc, curr) => acc + curr.count, 0);
  if (total === 0) return null;

  return (
    <div className="space-y-3 font-mono text-xs">
      <div className="text-[#9A9A91] text-[11px] uppercase tracking-wider">
        Identified Provider Volume Distribution
      </div>
      <div className="space-y-2.5">
        {items.map((item, idx) => {
          const pct = item.percentage ?? Math.round((item.count / total) * 100);
          return (
            <div key={idx} className="space-y-1">
              <div className="flex items-center justify-between text-[#F4F4F0]">
                <span className="font-bold">{item.provider}</span>
                <span className="text-[#9A9A91]">
                  {item.count.toLocaleString()} calls ({pct}%)
                </span>
              </div>
              <div className="w-full bg-[#0D0D0D] border border-[#333330] h-2">
                <div
                  className="bg-[#FFCC00] h-full transition-all duration-150"
                  style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
