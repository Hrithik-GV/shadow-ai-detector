import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Radio, Database, ShieldAlert, Shield } from 'lucide-react';

const navItems = [
  {
    name: 'Overview',
    to: '/',
    icon: LayoutDashboard,
  },
  {
    name: 'AI Traffic',
    to: '/traffic',
    icon: Radio,
  },
  {
    name: 'AI Inventory',
    to: '/inventory',
    icon: Database,
  },
  {
    name: 'Risk Analysis',
    to: '/risk',
    icon: ShieldAlert,
  },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col shrink-0 min-h-screen">
      {/* Brand logo header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800 space-x-3">
        <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          <Shield className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <span className="font-bold text-slate-100 tracking-wide text-sm block">Shadow AI</span>
          <span className="text-[10px] font-mono text-indigo-400 tracking-wider uppercase block">Detector</span>
        </div>
      </div>

      {/* Navigation list */}
      <nav className="p-4 space-y-1.5 flex-1">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          Security Console
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800/80 text-[11px] text-slate-400">
        <div className="flex items-center space-x-1.5 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>Core Engine v0.1.0</span>
        </div>
      </div>
    </aside>
  );
};
