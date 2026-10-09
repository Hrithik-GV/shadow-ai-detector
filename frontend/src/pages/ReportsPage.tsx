import React from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { useReportMetrics } from '../hooks/useReports';
import {
  FileText,
  RefreshCw,
  Clock,
  Database,
  Crosshair,
  Radar,
  Percent,
  CheckCircle,
} from 'lucide-react';

export interface ReportsPageProps {
  retry?: boolean | number;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ retry }) => {
  const { data: metrics, isLoading, isError, error, refetch, isFetching } = useReportMetrics({ retry });

  // Extract actual backend fields without inventing values
  const precision = metrics?.precision ?? metrics?.detectionPrecision;
  const recall = metrics?.recall ?? metrics?.detectionRecall;
  const falsePositiveRate = metrics?.falsePositiveRate ?? metrics?.fpr;
  const providerAccuracy = metrics?.providerAccuracy ?? metrics?.providerIdentificationAccuracy;
  const datasetSize = metrics?.datasetSize ?? metrics?.evaluatedRecordsCount ?? metrics?.totalEvaluations;
  const evaluationTimestamp = metrics?.evaluatedAt ?? metrics?.lastGeneratedAt ?? metrics?.timestamp;

  const hasAnyMetric =
    precision !== undefined ||
    recall !== undefined ||
    falsePositiveRate !== undefined ||
    providerAccuracy !== undefined ||
    datasetSize !== undefined ||
    metrics?.detectionAccuracy !== undefined;

  const formatPercentage = (val: number | undefined) => {
    if (val === undefined) return 'Not available';
    const num = val > 1 ? val : val * 100;
    return `${num.toFixed(1)}%`;
  };

  return (
    <PageContainer
      title="Test Reports"
      description="Historical model detection accuracy, precision, recall benchmarks, and dataset evaluation metrics from GET /api/reports/metrics."
      badge={
        <Badge variant={hasAnyMetric ? 'accent' : 'default'}>
          {hasAnyMetric ? 'REPORT LOADED' : 'GET /api/reports/metrics'}
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
          REFRESH REPORT
        </Button>
      }
    >
      {/* Loading State */}
      {isLoading && <LoadingState message="FETCHING EVALUATION METRICS FROM GET /api/reports/metrics..." />}

      {/* Error State */}
      {isError && (
        <QueryErrorState
          title="Reports API Error"
          error={error}
          onRetry={() => refetch()}
          isRetrying={isFetching}
        />
      )}

      {/* Actual Evaluation Metrics Section */}
      {!isLoading && !isError && metrics && hasAnyMetric && (
        <div className="space-y-6">
          {/* Metadata Banner */}
          <Card
            variant="charcoal"
            title="Evaluation Benchmark Summary"
            subtitle="Verified detection performance benchmarks executed against test network datasets."
            headerIcon={<CheckCircle className="w-5 h-5 text-[#00E575]" />}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 font-mono text-xs">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#0D0D0D] border border-[#333330] text-[#FFCC00]">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[#9A9A91] text-[10px] uppercase block">Test Dataset Size</span>
                  <span className="text-base font-bold text-[#F4F4F0]">
                    {datasetSize !== undefined ? `${datasetSize.toLocaleString()} records` : 'Not available'}
                  </span>
                </div>
              </div>

              {evaluationTimestamp && (
                <div className="flex items-center gap-2 text-[#9A9A91]">
                  <Clock className="w-3.5 h-3.5 text-[#FFCC00]" />
                  <span>Evaluation Timestamp: {evaluationTimestamp}</span>
                </div>
              )}
            </div>
          </Card>

          {/* Core Metrics Grid */}
          <div>
            <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#9A9A91] mb-3">
              Performance Indicators
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
              {/* 1. Detection Precision */}
              <Card variant="surface">
                <div className="flex items-center justify-between">
                  <span className="text-[#9A9A91] text-[10px] uppercase">Detection Precision</span>
                  <Crosshair className="w-4 h-4 text-[#FFCC00]" />
                </div>
                <div className="text-2xl font-bold text-[#00E575] mt-1">
                  {formatPercentage(precision)}
                </div>
                <p className="text-[11px] text-[#9A9A91] mt-1">
                  Accuracy of identified AI flows
                </p>
              </Card>

              {/* 2. Detection Recall */}
              <Card variant="surface">
                <div className="flex items-center justify-between">
                  <span className="text-[#9A9A91] text-[10px] uppercase">Detection Recall</span>
                  <Radar className="w-4 h-4 text-[#FFCC00]" />
                </div>
                <div className="text-2xl font-bold text-[#FFCC00] mt-1">
                  {formatPercentage(recall)}
                </div>
                <p className="text-[11px] text-[#9A9A91] mt-1">
                  Coverage of real AI packet streams
                </p>
              </Card>

              {/* 3. False-Positive Rate */}
              <Card variant="surface">
                <div className="flex items-center justify-between">
                  <span className="text-[#9A9A91] text-[10px] uppercase">False-Positive Rate</span>
                  <Percent className="w-4 h-4 text-[#FF6B6B]" />
                </div>
                <div className="text-2xl font-bold text-[#FF6B6B] mt-1">
                  {formatPercentage(falsePositiveRate)}
                </div>
                <p className="text-[11px] text-[#9A9A91] mt-1">
                  Benign traffic misclassified as AI
                </p>
              </Card>

              {/* 4. Provider Identification Accuracy */}
              <Card variant="surface">
                <div className="flex items-center justify-between">
                  <span className="text-[#9A9A91] text-[10px] uppercase">Provider Accuracy</span>
                  <Database className="w-4 h-4 text-[#00E575]" />
                </div>
                <div className="text-2xl font-bold text-[#F4F4F0] mt-1">
                  {formatPercentage(providerAccuracy)}
                </div>
                <p className="text-[11px] text-[#9A9A91] mt-1">
                  Correct vendor & model mapping
                </p>
              </Card>
            </div>
          </div>

          {/* Optional Categories Breakdown if supplied by backend */}
          {metrics.categoriesBreakdown && Object.keys(metrics.categoriesBreakdown).length > 0 && (
            <Card
              variant="charcoal"
              title="Category Breakdown"
              subtitle="Evaluation scores categorized by tool classification."
            >
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                {Object.entries(metrics.categoriesBreakdown).map(([cat, score]) => (
                  <div key={cat} className="p-3 bg-[#0D0D0D] border border-[#333330]">
                    <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">{cat}</span>
                    <span className="text-base font-bold text-[#FFCC00]">{score}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Honest Empty State: when no evaluation results exist */}
      {!isLoading && !isError && (!metrics || !hasAnyMetric) && (
        <EmptyState
          title="No evaluation results available."
          description="Evaluation benchmark tests have not been executed or no report metrics have been recorded by the detection backend yet."
          statusLabel="REPORT EMPTY"
          icon={<FileText className="w-7 h-7" />}
          action={
            <Button
              variant="secondary"
              size="md"
              icon={<RefreshCw className="w-3.5 h-3.5" />}
              onClick={() => refetch()}
            >
              CHECK FOR NEW BENCHMARK
            </Button>
          }
        />
      )}
    </PageContainer>
  );
};
