import React from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { FileText, Download, Play } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  return (
    <PageContainer
      title="Test Reports"
      description="Historical security audit reports, automated policy tests, and compliance summaries."
      badge={<Badge variant="default">0 REPORTS</Badge>}
      actions={
        <Button
          variant="primary"
          size="sm"
          icon={<Play className="w-3.5 h-3.5" />}
        >
          GENERATE REPORT
        </Button>
      }
    >
      <EmptyState
        title="No Test Reports Generated"
        description="Security assessment and compliance audit reports will be available for export once traffic analysis data is recorded."
        statusLabel="ARCHIVE EMPTY"
        icon={<FileText className="w-7 h-7" />}
        action={
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#0D0D0D] border border-[#333330] text-[11px] font-mono text-[#9A9A91]">
            <Download className="w-3.5 h-3.5 text-[#FFCC00]" />
            <span>Reports will be exportable in CSV and JSON formats</span>
          </div>
        }
      />
    </PageContainer>
  );
};
