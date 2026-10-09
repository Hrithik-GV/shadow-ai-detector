import React from 'react';
import { StatusBadge } from './StatusBadge';
import { ShieldCheck } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="h-16 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center space-x-3">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
          Enterprise Security
        </span>
        <span className="text-slate-400 text-sm hidden sm:inline">|</span>
        <span className="text-xs text-slate-400 hidden sm:inline">Network AI Ingestion & Classification Console</span>
      </div>

      <div className="flex items-center space-x-4">
        <StatusBadge />
        <div className="p-2 text-slate-400 hover:text-slate-200" title="Security policy active">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
        </div>
      </div>
    </header>
  );
};
