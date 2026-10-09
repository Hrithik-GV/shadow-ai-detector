import React from 'react';
import { ShieldAlert, Terminal } from 'lucide-react';
import { Badge } from './Badge';

export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  statusLabel?: string;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
  statusLabel = 'AWAITING INGESTION',
  className = '',
}) => {
  return (
    <div
      className={`border border-[#333330] bg-[#171716] shadow-[4px_4px_0_#000000] p-8 sm:p-12 text-center relative overflow-hidden ${className}`}
    >
      {/* Pixel corner bracket accents */}
      <div className="absolute top-2 left-2 w-2 h-2 border-t-2 border-l-2 border-[#FFCC00]/50" />
      <div className="absolute top-2 right-2 w-2 h-2 border-t-2 border-r-2 border-[#FFCC00]/50" />
      <div className="absolute bottom-2 left-2 w-2 h-2 border-b-2 border-l-2 border-[#FFCC00]/50" />
      <div className="absolute bottom-2 right-2 w-2 h-2 border-b-2 border-r-2 border-[#FFCC00]/50" />

      <div className="max-w-md mx-auto flex flex-col items-center">
        {/* Icon container */}
        <div className="w-14 h-14 bg-[#181818] border-2 border-[#333330] shadow-[3px_3px_0_#000000] flex items-center justify-center text-[#FFCC00] mb-5">
          {icon || <Terminal className="w-7 h-7" />}
        </div>

        {/* Status indicator badge */}
        <div className="mb-3">
          <Badge variant="accent" size="sm" icon={<span className="w-1.5 h-1.5 bg-[#FFCC00] inline-block animate-pulse" />}>
            {statusLabel}
          </Badge>
        </div>

        {/* Title */}
        <h3 className="font-mono text-base sm:text-lg font-bold text-[#F4F4F0] tracking-wide mb-2">
          {title}
        </h3>

        {/* Description */}
        <p className="font-mono text-xs sm:text-sm text-[#9A9A91] leading-relaxed mb-6">
          {description}
        </p>

        {/* Action slot or guidance */}
        {action ? (
          <div>{action}</div>
        ) : (
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#0D0D0D] border border-[#333330] text-[11px] font-mono text-[#9A9A91]">
            <ShieldAlert className="w-3.5 h-3.5 text-[#FFCC00]" />
            <span>Connect sensor agent to ingest real data</span>
          </div>
        )}
      </div>
    </div>
  );
};
