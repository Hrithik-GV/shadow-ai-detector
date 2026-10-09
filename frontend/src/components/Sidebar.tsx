import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Radio,
  Database,
  ShieldAlert,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
} from 'lucide-react';

export interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

const navItems = [
  {
    name: 'Overview',
    to: '/',
    icon: LayoutDashboard,
    badge: undefined,
  },
  {
    name: 'Traffic Analysis',
    to: '/traffic',
    icon: Radio,
    badge: 'LIVE',
  },
  {
    name: 'AI Inventory',
    to: '/inventory',
    icon: Database,
    badge: undefined,
  },
  {
    name: 'Risk Findings',
    to: '/risks',
    icon: ShieldAlert,
    badge: undefined,
  },
  {
    name: 'Test Reports',
    to: '/reports',
    icon: FileText,
    badge: undefined,
  },
  {
    name: 'Settings',
    to: '/settings',
    icon: Settings,
    badge: undefined,
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile,
}) => {
  return (
    <>
      {/* Mobile backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/80 z-40 md:hidden"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 bg-[#121212] border-r-2 border-[#333330] flex flex-col shrink-0 transition-all duration-200 ease-in-out ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        } ${isCollapsed ? 'w-18' : 'w-64'}`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b-2 border-[#333330] bg-[#0D0D0D]">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-8 h-8 bg-[#181818] border-2 border-[#FFCC00] shadow-[2px_2px_0_#735C00] flex items-center justify-center shrink-0">
              <Shield className="w-4 h-4 text-[#FFCC00]" />
            </div>
            {!isCollapsed && (
              <div className="truncate">
                <span className="font-pixel text-[11px] text-[#F4F4F0] tracking-wider block">
                  SHADOW AI
                </span>
                <span className="font-mono text-[10px] text-[#FFCC00] tracking-widest block uppercase">
                  DETECTOR SEC
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Navigation list */}
        <nav className="p-3 space-y-1.5 flex-1 overflow-y-auto">
          {!isCollapsed && (
            <div className="px-3 py-2 text-[10px] font-mono font-bold text-[#9A9A91] uppercase tracking-wider">
              OPS CONSOLE
            </div>
          )}
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={onCloseMobile}
                title={isCollapsed ? item.name : undefined}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 font-mono text-xs font-medium uppercase tracking-wider transition-all select-none ${
                    isActive
                      ? 'bg-[#181818] text-[#FFCC00] border-l-4 border-l-[#FFCC00] border-y border-r border-[#333330] shadow-[2px_2px_0_#000000] font-bold'
                      : 'text-[#9A9A91] hover:text-[#F4F4F0] hover:bg-[#181818]/60 border border-transparent'
                  } ${isCollapsed ? 'justify-center px-0' : ''}`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                {!isCollapsed && (
                  <span className="truncate flex-1">{item.name}</span>
                )}
                {!isCollapsed && item.badge && (
                  <span className="text-[9px] font-mono px-1.5 py-0.2 bg-[#FFCC00]/15 text-[#FFCC00] border border-[#FFCC00] leading-tight">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer with collapse toggle */}
        <div className="p-3 border-t-2 border-[#333330] bg-[#0D0D0D]">
          <button
            onClick={onToggleCollapse}
            className="w-full hidden md:flex items-center justify-center gap-2 py-2 px-2 bg-[#181818] hover:bg-[#222222] border border-[#333330] text-[#9A9A91] hover:text-[#F4F4F0] font-mono text-xs uppercase tracking-wider shadow-[2px_2px_0_#000000] active:translate-x-[1px] active:translate-y-[1px] cursor-pointer"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4 text-[#FFCC00]" />
            ) : (
              <>
                <ChevronLeft className="w-4 h-4 text-[#FFCC00]" />
                <span>COLLAPSE</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
};
