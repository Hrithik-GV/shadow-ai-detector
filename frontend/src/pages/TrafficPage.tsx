import React from 'react';
import { TrafficMonitor } from '../features/traffic/TrafficMonitor';

export const TrafficPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">AI Traffic Monitor</h1>
          <p className="text-xs text-slate-400">Discover and inspect network traffic destined for AI providers.</p>
        </div>
      </div>
      <TrafficMonitor />
    </div>
  );
};
