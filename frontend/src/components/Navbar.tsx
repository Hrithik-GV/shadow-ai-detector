import React from 'react';
import { useLocation } from 'react-router-dom';
import { StatusBadge } from './StatusBadge';
import { Menu, Shield } from 'lucide-react';

export interface NavbarProps {
  onOpenMobile: () => void;
}

const routeTitles: Record<string, { title: string; breadcrumb: string }> = {
  '/': { title: 'Overview', breadcrumb: 'CONSOLE > OVERVIEW' },
  '/traffic': { title: 'Traffic Analysis', breadcrumb: 'CONSOLE > TRAFFIC ANALYSIS' },
  '/inventory': { title: 'AI Inventory', breadcrumb: 'CONSOLE > AI INVENTORY' },
  '/risks': { title: 'Risk Findings', breadcrumb: 'CONSOLE > RISK FINDINGS' },
  '/reports': { title: 'Test Reports', breadcrumb: 'CONSOLE > TEST REPORTS' },
  '/settings': { title: 'Settings', breadcrumb: 'CONSOLE > SETTINGS' },
};

export const Navbar: React.FC<NavbarProps> = ({ onOpenMobile }) => {
  const location = useLocation();
  const currentRoute = routeTitles[location.pathname] || {
    title: 'Page Not Found',
    breadcrumb: 'CONSOLE > 404 NOT FOUND',
  };

  return (
    <header className="h-16 bg-[#121212] border-b-2 border-[#333330] px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Mobile hamburger & Breadcrumbs / Page Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobile}
          className="md:hidden p-2 bg-[#181818] border border-[#333330] text-[#F4F4F0] hover:border-[#FFCC00] focus:outline-none"
          aria-label="Open navigation menu"
        >
          <Menu className="w-4 h-4 text-[#FFCC00]" />
        </button>

        <div>
          <div className="font-mono text-[10px] text-[#9A9A91] tracking-widest uppercase flex items-center gap-1.5">
            <Shield className="w-3 h-3 text-[#FFCC00]" />
            <span>{currentRoute.breadcrumb}</span>
          </div>
          <h2 className="font-mono text-sm sm:text-base font-bold text-[#F4F4F0] tracking-wide uppercase">
            {currentRoute.title}
          </h2>
        </div>
      </div>

      {/* Right: API status badge */}
      <div className="flex items-center gap-3">
        <StatusBadge />
      </div>
    </header>
  );
};
