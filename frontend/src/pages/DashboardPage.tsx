import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { API_BASE_URL } from '../lib/config';
import {
  Radio,
  Database,
  ShieldAlert,
  FileText,
  Server,
  ArrowRight,
  Sliders,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageContainer
      title="Overview"
      description="Central operations console for discovering unauthorized AI usage, cataloging providers, and evaluating enterprise risk."
      badge={<Badge variant="accent">CONSOLE READY</Badge>}
      actions={
        <Button
          variant="secondary"
          size="sm"
          icon={<Sliders className="w-3.5 h-3.5" />}
          onClick={() => navigate('/settings')}
        >
          CONFIGURE AGENT
        </Button>
      }
    >
      {/* System Ingestion Target Card */}
      <Card
        variant="charcoal"
        title="Ingestion Engine Target"
        subtitle="Connected API gateway endpoint for live traffic mirror and discovery scan ingestion."
        headerIcon={<Server className="w-5 h-5 text-[#FFCC00]" />}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 font-mono text-xs">
          <div className="space-y-1">
            <span className="text-[#9A9A91] uppercase tracking-wider block text-[10px]">Configured URL</span>
            <span className="text-[#F4F4F0] font-bold text-sm bg-[#0D0D0D] px-3 py-1.5 border border-[#333330] inline-block">
              {API_BASE_URL}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="muted">PORT 8000</Badge>
            <Badge variant="accent">VITE_API_BASE_URL</Badge>
          </div>
        </div>
      </Card>

      {/* Module Overview Navigation Grid */}
      <div>
        <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#9A9A91] mb-3">
          Security Modules
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card
            hoverable
            title="Traffic Analysis"
            subtitle="Deep packet and DNS discovery"
            headerIcon={<Radio className="w-4 h-4 text-[#FFCC00]" />}
          >
            <p className="font-mono text-xs text-[#9A9A91] mb-4">
              Inspect outbound API requests destined for AI foundation providers.
            </p>
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => navigate('/traffic')}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              OPEN TRAFFIC
            </Button>
          </Card>

          <Card
            hoverable
            title="AI Inventory"
            subtitle="Catalog and endpoint tracker"
            headerIcon={<Database className="w-4 h-4 text-[#FFCC00]" />}
          >
            <p className="font-mono text-xs text-[#9A9A91] mb-4">
              Audit discovered generative AI models, tools, and shadow credentials.
            </p>
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => navigate('/inventory')}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              VIEW INVENTORY
            </Button>
          </Card>

          <Card
            hoverable
            title="Risk Findings"
            subtitle="Policy & data egress checks"
            headerIcon={<ShieldAlert className="w-4 h-4 text-[#FFCC00]" />}
          >
            <p className="font-mono text-xs text-[#9A9A91] mb-4">
              Review policy violations, unapproved shadow AI tools, and risks.
            </p>
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => navigate('/risks')}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              VIEW RISKS
            </Button>
          </Card>

          <Card
            hoverable
            title="Test Reports"
            subtitle="Audit trails and export logs"
            headerIcon={<FileText className="w-4 h-4 text-[#FFCC00]" />}
          >
            <p className="font-mono text-xs text-[#9A9A91] mb-4">
              Generate compliance audits and export detection summaries.
            </p>
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => navigate('/reports')}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              VIEW REPORTS
            </Button>
          </Card>
        </div>
      </div>

      {/* Honest Empty State for Initial Ingestion */}
      <EmptyState
        title="No Live Telemetry Stream Active"
        description="The detection console is initialized and waiting for real network packet mirrors or collector logs. Once connected to the backend ingestion pipeline, real-time discovery events will appear."
        statusLabel="STANDBY / NO DATA"
        action={
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/traffic')}
          >
            MONITOR TRAFFIC INGESTION
          </Button>
        }
      />
    </PageContainer>
  );
};
