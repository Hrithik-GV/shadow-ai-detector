import React from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { useReportMetrics } from '../hooks/useReports';
import { FileText, Download, RefreshCw } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const { data: metrics, isLoading, isError, error, refetch, isFetching } = useReportMetrics();

  return (
    <PageContainer
      title="Test Reports"
      description="Historical security audit reports, automated policy tests, and model evaluation metrics."
      badge={
        <Badge variant={metrics ? 'accent' : 'default'}>
          {metrics ? `${metrics.totalEvaluations} EVALS` : 'GET /api/reports/metrics'}
        </Badge>
      }
      actions={
        <Button
          variant="secondary"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          icon={<RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />}
        >
          REFRESH METRICS
        </Button>
      }
    >
      {isLoading && <LoadingState message="FETCHING EVALUATION METRICS FROM BACKEND..." />}

      {isError && (
        <QueryErrorState
          title="Reports API Error"
          error={error}
          onRetry={() => refetch()}
          isRetrying={isFetching}
        />
      )}

      {metrics && !isLoading && !isError && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card variant="surface">
              <div className="text-[10px] font-mono uppercase text-[#9A9A91]">Total Evaluations</div>
              <div className="text-2xl font-mono font-bold text-[#F4F4F0] mt-1">
                {metrics.totalEvaluations}
              </div>
            </Card>
            <Card variant="surface">
              <div className="text-[10px] font-mono uppercase text-[#9A9A91]">Detection Accuracy</div>
              <div className="text-2xl font-mono font-bold text-[#00E575] mt-1">
                {metrics.detectionAccuracy !== undefined ? `${(metrics.detectionAccuracy * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </Card>
            <Card variant="surface">
              <div className="text-[10px] font-mono uppercase text-[#9A9A91]">False Positive Rate</div>
              <div className="text-2xl font-mono font-bold text-[#FFCC00] mt-1">
                {metrics.falsePositiveRate !== undefined ? `${(metrics.falsePositiveRate * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </Card>
            <Card variant="surface">
              <div className="text-[10px] font-mono uppercase text-[#9A9A91]">Avg Latency</div>
              <div className="text-2xl font-mono font-bold text-[#F4F4F0] mt-1">
                {metrics.averageLatencyMs !== undefined ? `${metrics.averageLatencyMs} ms` : 'N/A'}
              </div>
            </Card>
          </div>
        </div>
      )}

      {!metrics && !isLoading && !isError && (
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
      )}
    </PageContainer>
  );
};
