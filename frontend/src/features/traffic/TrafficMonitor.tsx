import React from 'react';
import { Activity, Radio, ShieldAlert } from 'lucide-react';

export const TrafficMonitor: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="border border-slate-800 bg-slate-900/60 backdrop-blur rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Radio className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100">AI Traffic Telemetry</h2>
              <p className="text-sm text-slate-400">
                Live packet stream and DNS resolution for AI services and unknown API gateways.
              </p>
            </div>
          </div>
        </div>

        {/* Empty state container awaiting backend integration */}
        <div className="mt-8 flex flex-col items-center justify-center p-12 text-center border border-dashed border-slate-800 rounded-lg bg-slate-950/40">
          <div className="p-3 bg-slate-900 text-slate-400 rounded-full mb-3">
            <Activity className="w-6 h-6 text-slate-500" />
          </div>
          <h3 className="text-sm font-medium text-slate-200">No active network telemetry stream</h3>
          <p className="text-xs text-slate-400 max-w-sm mt-1">
            Network traffic events will populate when the collector agent or proxy mirror is connected to the backend ingestion endpoint.
          </p>
          <div className="mt-4 inline-flex items-center text-xs font-mono px-3 py-1.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
            <ShieldAlert className="w-3.5 h-3.5 mr-2 text-amber-400" />
            Awaiting traffic ingestion stream
          </div>
        </div>
      </div>
    </div>
  );
};
