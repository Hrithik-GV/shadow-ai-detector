import React from 'react';
import { useApiHealth } from '../hooks/useApiHealth';
import { API_BASE_URL } from '../lib/config';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

export const StatusBadge: React.FC = () => {
  const { data, isLoading, isError } = useApiHealth();

  return (
    <div className="flex items-center space-x-2 text-xs font-mono bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-md">
      <span className="text-slate-400">Backend:</span>
      <span className="text-slate-300 truncate max-w-[150px]">{API_BASE_URL}</span>

      {isLoading && (
        <span className="inline-flex items-center text-amber-400 ml-1">
          <Loader2 className="w-3 h-3 animate-spin mr-1" />
          Connecting
        </span>
      )}

      {isError && (
        <span className="inline-flex items-center text-rose-400 ml-1" title="Backend not reachable at configured URL">
          <XCircle className="w-3 h-3 mr-1" />
          Offline
        </span>
      )}

      {data && !isLoading && !isError && (
        <span className="inline-flex items-center text-emerald-400 ml-1">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Connected
        </span>
      )}
    </div>
  );
};
