import React from 'react';
import { Link } from 'react-router-dom';
import { Radio, Database, ShieldAlert, ArrowRight, Server, Terminal } from 'lucide-react';
import { API_BASE_URL } from '../lib/config';

export const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Top Banner / System Shell Overview */}
      <div className="border border-slate-800 bg-slate-900/50 backdrop-blur rounded-xl p-6 lg:p-8">
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
          Shadow AI Detector Console
        </h1>
        <p className="mt-2 text-sm text-slate-400 max-w-2xl leading-relaxed">
          Continuous network inspection to uncover unauthorized AI model usage, catalog enterprise AI providers,
          and mitigate data leakage through automated risk classification.
        </p>

        <div className="mt-6 flex flex-wrap items-center gap-4 text-xs font-mono">
          <div className="flex items-center space-x-2 bg-slate-950 px-3 py-1.5 rounded border border-slate-800 text-slate-300">
            <Server className="w-3.5 h-3.5 text-indigo-400" />
            <span>Target API: {API_BASE_URL}</span>
          </div>
          <div className="flex items-center space-x-2 bg-slate-950 px-3 py-1.5 rounded border border-slate-800 text-slate-300">
            <Terminal className="w-3.5 h-3.5 text-emerald-400" />
            <span>Mode: Standby for ingestion</span>
          </div>
        </div>
      </div>

      {/* Core Modules Shell */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Core Security Modules
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* AI Traffic Monitor */}
          <Link
            to="/traffic"
            className="group block border border-slate-800 bg-slate-900/40 hover:bg-slate-900/70 hover:border-slate-700 transition-all rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Radio className="w-5 h-5" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
            </div>
            <h3 className="text-base font-semibold text-slate-200 group-hover:text-white">
              Traffic Discovery
            </h3>
            <p className="mt-1 text-xs text-slate-400 leading-relaxed">
              Detect and inspect outbound AI payload streams, LLM API calls, and shadow AI network flows.
            </p>
          </Link>

          {/* AI Inventory */}
          <Link
            to="/inventory"
            className="group block border border-slate-800 bg-slate-900/40 hover:bg-slate-900/70 hover:border-slate-700 transition-all rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Database className="w-5 h-5" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
            </div>
            <h3 className="text-base font-semibold text-slate-200 group-hover:text-white">
              Provider Inventory
            </h3>
            <p className="mt-1 text-xs text-slate-400 leading-relaxed">
              Catalog discovered generative AI services, custom LLM gateways, and third-party tools.
            </p>
          </Link>

          {/* Risk Classification */}
          <Link
            to="/risk"
            className="group block border border-slate-800 bg-slate-900/40 hover:bg-slate-900/70 hover:border-slate-700 transition-all rounded-xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400 group-hover:translate-x-1 transition-all" />
            </div>
            <h3 className="text-base font-semibold text-slate-200 group-hover:text-white">
              Risk Classification
            </h3>
            <p className="mt-1 text-xs text-slate-400 leading-relaxed">
              Evaluate policy compliance, unapproved shadow services, and data exposure levels.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
};
