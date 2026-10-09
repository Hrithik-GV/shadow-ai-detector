import React, { useState } from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { useApiHealth } from '../hooks/useApiHealth';
import { API_BASE_URL } from '../lib/config';
import {
  Server,
  Sliders,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Info,
  ShieldCheck,
  RotateCcw,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { data: healthData, isLoading, isError, refetch, isFetching } = useApiHealth();

  // Local client preference states (stored locally in localStorage)
  const [sidebarPreference, setSidebarPreference] = useState<string>(() => {
    return localStorage.getItem('shadow_ai_sidebar_collapsed') === 'true'
      ? 'collapsed'
      : 'expanded';
  });

  const [notificationState, setNotificationState] = useState<string | null>(null);

  const handleSidebarPreferenceChange = (val: string) => {
    setSidebarPreference(val);
    localStorage.setItem('shadow_ai_sidebar_collapsed', val === 'collapsed' ? 'true' : 'false');
    setNotificationState('Local preference saved. Reload to apply across entire session.');
    setTimeout(() => setNotificationState(null), 4000);
  };

  const handleResetPreferences = () => {
    localStorage.removeItem('shadow_ai_sidebar_collapsed');
    setSidebarPreference('expanded');
    setNotificationState('Local client preferences reset to defaults.');
    setTimeout(() => setNotificationState(null), 4000);
  };

  // Sanitize URL for display so no sensitive auth info (e.g. user:pass@) is exposed
  const sanitizedApiUrl = React.useMemo(() => {
    try {
      const parsed = new URL(API_BASE_URL);
      return `${parsed.protocol}//${parsed.host}${parsed.pathname}`;
    } catch {
      return API_BASE_URL;
    }
  }, []);

  return (
    <PageContainer
      title="Settings"
      description="Configure local frontend console preferences, verify API connectivity, and review client communication bindings."
      badge={<Badge variant="accent">SYS CONFIG</Badge>}
    >
      <div className="space-y-6">
        {notificationState && (
          <div className="p-3 bg-[#0D0D0D] border-2 border-[#FFCC00] text-[#FFCC00] font-mono text-xs flex items-center justify-between shadow-[3px_3px_0_#735C00]">
            <span>{notificationState}</span>
            <Button variant="outline" size="sm" onClick={() => setNotificationState(null)}>
              DISMISS
            </Button>
          </div>
        )}

        {/* 1. API Connectivity & Backend Binding */}
        <Card
          variant="charcoal"
          title="Backend Ingestion Binding"
          subtitle="Target URL used for REST queries, live packet telemetry, and status probes."
          headerIcon={<Server className="w-5 h-5 text-[#FFCC00]" />}
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              icon={<RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />}
            >
              RETEST CONNECTION
            </Button>
          }
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="space-y-1.5">
              <label className="text-[#9A9A91] text-[10px] uppercase tracking-wider block">
                Configured Backend Endpoint (VITE_API_BASE_URL)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  readOnly
                  value={sanitizedApiUrl}
                  className="flex-1 bg-[#0D0D0D] border border-[#333330] px-3 py-2 text-[#F4F4F0] font-mono text-xs select-all outline-none focus:border-[#FFCC00]"
                />
                <div className="shrink-0">
                  {isLoading && (
                    <Badge variant="warning" size="md" icon={<Loader2 className="w-3 h-3 animate-spin" />}>
                      CHECKING
                    </Badge>
                  )}
                  {isError && (
                    <Badge variant="danger" size="md" icon={<XCircle className="w-3 h-3" />}>
                      OFFLINE
                    </Badge>
                  )}
                  {healthData && !isLoading && !isError && (
                    <Badge variant="success" size="md" icon={<CheckCircle2 className="w-3 h-3" />}>
                      CONNECTED
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            <div className="p-3 bg-[#0D0D0D] border border-[#333330] text-[11px] text-[#9A9A91] space-y-1">
              <div className="flex items-center gap-1.5 text-[#F4F4F0]">
                <Info className="w-3.5 h-3.5 text-[#FFCC00]" />
                <span className="font-bold">Environment Configuration Guidance:</span>
              </div>
              <p>
                To bind the frontend to a remote or containerized detector, update{' '}
                <code className="text-[#FFCC00]">VITE_API_BASE_URL</code> in your{' '}
                <code className="text-[#FFCC00]">.env</code> file and restart Vite. Real secrets or tokens are never committed.
              </p>
            </div>
          </div>
        </Card>

        {/* 2. Client Interface Preferences (Local Storage) */}
        <Card
          variant="surface"
          title="Console Display Preferences"
          subtitle="Client-side interface options saved in your local browser storage."
          headerIcon={<Sliders className="w-5 h-5 text-[#FFCC00]" />}
          action={
            <Button
              variant="outline"
              size="sm"
              icon={<RotateCcw className="w-3.5 h-3.5" />}
              onClick={handleResetPreferences}
            >
              RESET DEFAULTS
            </Button>
          }
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-[#0D0D0D] border border-[#333330]">
              <div>
                <span className="text-[#F4F4F0] font-bold block">Navigation Sidebar Default</span>
                <span className="text-[#9A9A91] text-[11px]">
                  Choose whether the sidebar starts expanded or collapsed by default.
                </span>
              </div>
              <select
                value={sidebarPreference}
                onChange={(e) => handleSidebarPreferenceChange(e.target.value)}
                className="bg-[#171716] border border-[#333330] px-3 py-1.5 text-[#F4F4F0] font-mono text-xs focus:outline-none focus:border-[#FFCC00]"
              >
                <option value="expanded">EXPANDED (256px)</option>
                <option value="collapsed">COLLAPSED (72px)</option>
              </select>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-[#0D0D0D] border border-[#333330]">
              <div>
                <span className="text-[#F4F4F0] font-bold block">TanStack Query Cache Window</span>
                <span className="text-[#9A9A91] text-[11px]">
                  Default query freshness window before automatic background revalidation.
                </span>
              </div>
              <Badge variant="muted" size="md">
                60 SECONDS (DEFAULT)
              </Badge>
            </div>
          </div>
        </Card>

        {/* 3. Server-Side Policy Notice */}
        <Card
          variant="surface"
          title="Policy & Approval Enforcement"
          subtitle="Architectural information regarding security rules and approval workflows."
          headerIcon={<ShieldCheck className="w-5 h-5 text-[#FFCC00]" />}
        >
          <div className="p-3 bg-[#0D0D0D] border border-[#333330] text-[11px] font-mono text-[#9A9A91] space-y-2">
            <p className="text-[#F4F4F0] leading-relaxed">
              Provider approval status, risk threshold weights, and data loss prevention policies are strictly evaluated and governed by the backend detection service.
            </p>
            <p>
              In accordance with project constraints, the frontend does not implement mock approval buttons or fake policy editing toggles without corresponding backend management endpoints.
            </p>
          </div>
        </Card>
      </div>
    </PageContainer>
  );
};
