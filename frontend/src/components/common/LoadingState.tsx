import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'CONNECTING TO INGESTION API...',
  className = '',
}) => {
  return (
    <div
      className={`border-2 border-[#333330] bg-[#171716] shadow-[4px_4px_0_#000000] p-8 text-center flex flex-col items-center justify-center min-h-[220px] ${className}`}
    >
      <div className="w-10 h-10 bg-[#181818] border-2 border-[#FFCC00] shadow-[2px_2px_0_#735C00] flex items-center justify-center text-[#FFCC00] mb-4">
        <Loader2 className="w-5 h-5 animate-spin text-[#FFCC00]" />
      </div>
      <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#FFCC00] mb-1">
        {message}
      </div>
      <p className="font-mono text-[11px] text-[#9A9A91] tracking-wide">
        Querying backend pipeline. Please stand by...
      </p>
    </div>
  );
};
