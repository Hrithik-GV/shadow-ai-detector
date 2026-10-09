import React from 'react';
import { useApiHealth } from '../hooks/useApiHealth';
import { API_BASE_URL } from '../lib/config';
import { Loader2, RefreshCw } from 'lucide-react';

export const StatusBadge: React.FC = () => {
  const { data, isLoading, isError, refetch } = useApiHealth();

  return (
    <div className="flex items-center space-x-2 text-[11px] font-mono bg-[#181818] border border-[#333330] shadow-[2px_2px_0_#000000] px-2.5 py-1 text-[#F4F4F0]">
      <span className="text-[#9A9A91] uppercase tracking-wider hidden sm:inline">API:</span>
      <span className="text-[#F4F4F0] truncate max-w-[140px] font-semibold" title={API_BASE_URL}>
        {API_BASE_URL.replace(/^https?:\/\//, '')}
      </span>

      <span className="text-[#333330]">|</span>

      {isLoading && (
        <span className="inline-flex items-center text-[#FFCC00] gap-1">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span className="tracking-wider uppercase">CHECKING</span>
        </span>
      )}

      {isError && (
        <button
          onClick={() => refetch()}
          title="Backend unreachable. Click to retry connection check."
          className="inline-flex items-center text-[#FF6B6B] hover:text-[#FF8E8E] gap-1 cursor-pointer focus:outline-none"
        >
          <span className="w-2 h-2 bg-[#FF4D4D] inline-block shadow-[1px_1px_0_#000000]" />
          <span className="tracking-wider uppercase font-semibold">OFFLINE</span>
          <RefreshCw className="w-2.5 h-2.5 ml-0.5 text-[#9A9A91] hover:text-[#F4F4F0]" />
        </button>
      )}

      {data && !isLoading && !isError && (
        <span className="inline-flex items-center text-[#00E575] gap-1" title="API connected and active">
          <span className="w-2 h-2 bg-[#00E575] inline-block shadow-[1px_1px_0_#000000]" />
          <span className="tracking-wider uppercase font-semibold">CONNECTED</span>
        </span>
      )}
    </div>
  );
};
