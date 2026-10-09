import React from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { API_BASE_URL } from '../lib/config';
import { Server, Sliders, Shield } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <PageContainer
      title="Settings"
      description="Configure backend API connection bindings, collector agent parameters, and detection policies."
      badge={<Badge variant="accent">SYS CONFIG</Badge>}
    >
      <div className="space-y-6">
        {/* Backend API Configuration */}
        <Card
          variant="charcoal"
          title="Backend Ingestion Binding"
          subtitle="Configured host URL used for API queries and packet telemetry streams."
          headerIcon={<Server className="w-5 h-5 text-[#FFCC00]" />}
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="space-y-1.5">
              <label className="text-[#9A9A91] uppercase tracking-wider block text-[10px]">
                API Base URL (from VITE_API_BASE_URL)
              </label>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  readOnly
                  value={API_BASE_URL}
                  className="flex-1 bg-[#0D0D0D] border border-[#333330] px-3 py-2 text-[#F4F4F0] font-mono text-xs select-all outline-none focus:border-[#FFCC00]"
                />
                <Button variant="secondary" size="sm" onClick={() => window.location.reload()}>
                  RETEST CONNECTION
                </Button>
              </div>
            </div>
            <p className="text-[11px] text-[#9A9A91] leading-relaxed">
              To change this endpoint, update <code className="bg-[#0D0D0D] px-1 py-0.5 border border-[#333330] text-[#FFCC00]">VITE_API_BASE_URL</code> in your <code className="bg-[#0D0D0D] px-1 py-0.5 border border-[#333330] text-[#FFCC00]">.env</code> file and restart the Vite development server.
            </p>
          </div>
        </Card>

        {/* Network Collector Agent Settings */}
        <Card
          variant="surface"
          title="Telemetry Collector Configuration"
          subtitle="Settings for local TAP, eBPF agent, or mirrored interface stream."
          headerIcon={<Sliders className="w-5 h-5 text-[#FFCC00]" />}
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <span className="text-[#9A9A91] uppercase tracking-wider block text-[10px]">
                  Collector Mode
                </span>
                <span className="text-[#F4F4F0] bg-[#0D0D0D] border border-[#333330] px-3 py-2 block">
                  PASSIVE DNS & SNI INSPECTION
                </span>
              </div>
              <div className="space-y-1">
                <span className="text-[#9A9A91] uppercase tracking-wider block text-[10px]">
                  Ingestion Port
                </span>
                <span className="text-[#F4F4F0] bg-[#0D0D0D] border border-[#333330] px-3 py-2 block">
                  8000 (HTTP / SSE)
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Security Policy Rules */}
        <Card
          variant="surface"
          title="Default Detection Policy"
          subtitle="Global classification rules applied to detected AI traffic."
          headerIcon={<Shield className="w-5 h-5 text-[#FFCC00]" />}
        >
          <div className="space-y-3 font-mono text-xs text-[#9A9A91]">
            <div className="flex items-center justify-between p-3 bg-[#0D0D0D] border border-[#333330]">
              <span>Flag unknown external AI providers as UNAPPROVED</span>
              <Badge variant="accent">ENABLED</Badge>
            </div>
            <div className="flex items-center justify-between p-3 bg-[#0D0D0D] border border-[#333330]">
              <span>Alert on sensitive payload egress to unapproved LLMs</span>
              <Badge variant="accent">ENABLED</Badge>
            </div>
          </div>
        </Card>
      </div>
    </PageContainer>
  );
};
