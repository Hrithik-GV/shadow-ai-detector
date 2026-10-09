import React from 'react';
import { Database, Search } from 'lucide-react';

export const InventoryManager: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="border border-slate-800 bg-slate-900/60 backdrop-blur rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-100">Discovered AI Inventory</h2>
              <p className="text-sm text-slate-400">
                Identified AI foundation models, enterprise SaaS tools, and unapproved shadow endpoints.
              </p>
            </div>
          </div>
        </div>

        {/* Empty state container awaiting backend discovery scan */}
        <div className="mt-8 flex flex-col items-center justify-center p-12 text-center border border-dashed border-slate-800 rounded-lg bg-slate-950/40">
          <div className="p-3 bg-slate-900 text-slate-400 rounded-full mb-3">
            <Search className="w-6 h-6 text-slate-500" />
          </div>
          <h3 className="text-sm font-medium text-slate-200">No inventory entries registered</h3>
          <p className="text-xs text-slate-400 max-w-sm mt-1">
            Detected AI providers, API endpoints, and unauthorized tool accounts will appear here once discovered by inspection rules.
          </p>
          <div className="mt-4 inline-flex items-center text-xs font-mono px-3 py-1.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
            Catalog status: Standby
          </div>
        </div>
      </div>
    </div>
  );
};
