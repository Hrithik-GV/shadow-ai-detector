import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/common/PageContainer';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { ActivityTimelineChart } from '../components/dashboard/ActivityTimelineChart';
import { ProviderDistributionBars } from '../components/dashboard/ProviderDistributionBars';
import { useDashboardStats } from '../hooks/useDashboardStats';
import { API_BASE_URL } from '../lib/config';
import {
  Radio,
  Database,
  ShieldAlert,
  Server,
  ArrowRight,
  RefreshCw,
  Upload,
  AlertTriangle,
  Clock,
  ExternalLink,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: stats, isLoading, isError, error, refetch, isFetching } = useDashboardStats();

  // Safely extract backend numbers without fabricating any defaults
  const totalTraffic =
    stats?.valid_records ??
    stats?.total_records_received ??
    stats?.totalAnalyzedRecords ??
    stats?.totalTrafficEvents ??
    stats?.totalTrafficRecords;

  const aiRelatedRecords =
    stats?.aiRelatedRecords ??
    stats?.aiTrafficEvents ??
    stats?.aiFlowsCount;

  const totalEndpoints =
    stats?.totalAiEndpoints ??
    stats?.totalEndpoints;

  const activeProviders =
    stats?.activeProvidersCount ??
    stats?.totalProviders;

  const unapprovedEndpoints = stats?.unapprovedEndpointsCount;

  const flaggedRisks = stats?.flaggedRiskCount;

  const highRisks = stats?.riskBreakdown?.high ?? stats?.highRiskCount;
  const mediumRisks = stats?.riskBreakdown?.medium ?? stats?.mediumRiskCount;
  const lowRisks = stats?.riskBreakdown?.low ?? stats?.lowRiskCount;
  const criticalRisks = stats?.riskBreakdown?.critical ?? stats?.criticalRiskCount;

  const lastTimestamp = stats?.lastAnalysisTimestamp || stats?.latest_timestamp;

  const distributionData =
    stats?.providerDistribution ||
    (stats?.protocol_distribution && Object.keys(stats.protocol_distribution).length > 0
      ? stats.protocol_distribution
      : undefined);

  // Has risk breakdown data from backend
  const hasRiskBreakdown =
    criticalRisks !== undefined ||
    highRisks !== undefined ||
    mediumRisks !== undefined ||
    lowRisks !== undefined;

  // Determine if backend data represents an unpopulated / initial first-use state
  const isFirstUse =
    stats &&
    (totalTraffic === 0 || totalTraffic === undefined) &&
    (totalEndpoints === 0 || totalEndpoints === undefined) &&
    (activeProviders === 0 || activeProviders === undefined) &&
    (flaggedRisks === 0 || flaggedRisks === undefined);

  return (
    <PageContainer
      title="Overview"
      description="Live operational telemetry and risk summary for organizational Shadow AI detection. Every metric is strictly sourced from GET /api/dashboard/stats."
      badge={
        <Badge variant={stats ? 'accent' : 'default'}>
          {stats ? 'LIVE TELEMETRY' : 'GET /api/dashboard/stats'}
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
          REFRESH TELEMETRY
        </Button>
      }
    >
      {/* Target Ingestion Endpoint Banner */}
      <Card
        variant="charcoal"
        title="Detection Engine Target"
        subtitle="Connected backend server endpoint queried via centralized Axios client."
        headerIcon={<Server className="w-5 h-5 text-[#FFCC00]" />}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 font-mono text-xs">
          <div className="space-y-1">
            <span className="text-[#9A9A91] text-[10px] uppercase tracking-wider block">
              Active Backend Base URL
            </span>
            <span className="text-[#F4F4F0] font-bold text-sm bg-[#0D0D0D] px-3 py-1.5 border border-[#333330] inline-block">
              {API_BASE_URL}
            </span>
          </div>
          {lastTimestamp && (
            <div className="flex items-center gap-2 text-[#9A9A91]">
              <Clock className="w-3.5 h-3.5 text-[#FFCC00]" />
              <span>Last Analysis: {lastTimestamp}</span>
            </div>
          )}
        </div>
      </Card>

      {/* Loading State */}
      {isLoading && <LoadingState message="FETCHING SUMMARY METRICS FROM GET /api/dashboard/stats..." />}

      {/* Error and Retry State */}
      {isError && (
        <QueryErrorState
          title="Dashboard Telemetry Unavailable"
          error={error}
          onRetry={() => refetch()}
          isRetrying={isFetching}
        />
      )}

      {/* First-Use Empty State: displayed when backend responds with zero data */}
      {!isLoading && !isError && isFirstUse && (
        <EmptyState
          title="No Traffic Telemetry Has Been Analyzed Yet"
          description="The detection engine is standing by. Submit your first network capture file (.csv, .json) in the Traffic Analysis module to discover AI providers, classify risk levels, and monitor endpoints."
          statusLabel="FIRST-USE / ZERO RECORDS"
          icon={<Radio className="w-7 h-7" />}
          action={
            <Button
              variant="primary"
              size="md"
              icon={<Upload className="w-3.5 h-3.5" />}
              onClick={() => navigate('/traffic')}
            >
              UPLOAD TRAFFIC FILE FOR ANALYSIS
            </Button>
          }
        />
      )}

      {/* Main Metrics Content: only rendered from real backend response */}
      {!isLoading && !isError && stats && !isFirstUse && (
        <div className="space-y-6">
          {/* Top-Level Metric Cards Grid */}
          <div>
            <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#9A9A91] mb-3">
              Operational Statistics
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
              {/* 1. Total Analyzed Traffic Records */}
              <Card variant="surface">
                <span className="text-[#9A9A91] text-[10px] uppercase block">
                  Total Analyzed Traffic
                </span>
                <span className="text-2xl font-bold text-[#F4F4F0] block mt-1">
                  {totalTraffic !== undefined ? totalTraffic.toLocaleString() : 'Not available'}
                </span>
                <span className="text-[11px] text-[#9A9A91] block mt-1">
                  Network packets inspected
                </span>
              </Card>

              {/* 2. AI-Related Records */}
              <Card variant="surface">
                <span className="text-[#9A9A91] text-[10px] uppercase block">
                  AI-Related Telemetry
                </span>
                <span className="text-2xl font-bold text-[#FFCC00] block mt-1">
                  {aiRelatedRecords !== undefined ? aiRelatedRecords.toLocaleString() : 'Not available'}
                </span>
                <span className="text-[11px] text-[#9A9A91] block mt-1">
                  Outbound AI connections
                </span>
              </Card>

              {/* 3. Identified Providers and Endpoints */}
              <Card variant="surface">
                <span className="text-[#9A9A91] text-[10px] uppercase block">
                  Providers & Endpoints
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-2xl font-bold text-[#F4F4F0]">
                    {activeProviders !== undefined ? activeProviders : '—'}
                  </span>
                  <span className="text-xs text-[#9A9A91]">providers /</span>
                  <span className="text-2xl font-bold text-[#FFCC00]">
                    {totalEndpoints !== undefined ? totalEndpoints : '—'}
                  </span>
                  <span className="text-xs text-[#9A9A91]">endpoints</span>
                </div>
                {unapprovedEndpoints !== undefined && (
                  <span className="text-[11px] text-[#FF6B6B] block mt-1 font-bold">
                    {unapprovedEndpoints} unapproved shadow services
                  </span>
                )}
              </Card>

              {/* 4. Total Flagged Risk Findings */}
              <Card variant="surface">
                <span className="text-[#9A9A91] text-[10px] uppercase block">
                  Flagged Risk Findings
                </span>
                <span className="text-2xl font-bold text-[#FF6B6B] block mt-1">
                  {flaggedRisks !== undefined ? flaggedRisks.toLocaleString() : 'Not available'}
                </span>
                <span className="text-[11px] text-[#9A9A91] block mt-1">
                  Policy & egress evaluations
                </span>
              </Card>
            </div>
          </div>

          {/* 4. Risk Breakdown Cards (High, Medium, Low, Critical) */}
          {hasRiskBreakdown && (
            <Card
              variant="charcoal"
              title="Risk Severity Classifications"
              subtitle="Breakdown of flagged findings by severity level returned by backend detection rules."
              headerIcon={<AlertTriangle className="w-5 h-5 text-[#FFCC00]" />}
            >
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono text-xs">
                {criticalRisks !== undefined && (
                  <div className="p-3 bg-[#0D0D0D] border border-[#8C2323]">
                    <span className="text-[#FF4D4D] text-[10px] uppercase font-bold block">
                      Critical Risk
                    </span>
                    <span className="text-xl font-bold text-[#FF4D4D] block mt-1">
                      {criticalRisks.toLocaleString()}
                    </span>
                  </div>
                )}
                {highRisks !== undefined && (
                  <div className="p-3 bg-[#0D0D0D] border border-[#8C2323]">
                    <span className="text-[#FF6B6B] text-[10px] uppercase font-bold block">
                      High Risk
                    </span>
                    <span className="text-xl font-bold text-[#FF6B6B] block mt-1">
                      {highRisks.toLocaleString()}
                    </span>
                  </div>
                )}
                {mediumRisks !== undefined && (
                  <div className="p-3 bg-[#0D0D0D] border border-[#997A00]">
                    <span className="text-[#FFCC00] text-[10px] uppercase font-bold block">
                      Medium Risk
                    </span>
                    <span className="text-xl font-bold text-[#FFCC00] block mt-1">
                      {mediumRisks.toLocaleString()}
                    </span>
                  </div>
                )}
                {lowRisks !== undefined && (
                  <div className="p-3 bg-[#0D0D0D] border border-[#333330]">
                    <span className="text-[#9A9A91] text-[10px] uppercase block">
                      Low Risk
                    </span>
                    <span className="text-xl font-bold text-[#F4F4F0] block mt-1">
                      {lowRisks.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* 5. Historical Activity Chart (rendered only when backend supplies real data) */}
          {stats.activityOverTime && stats.activityOverTime.length >= 2 && (
            <Card
              variant="charcoal"
              title="Traffic & Endpoint Activity Over Time"
              subtitle="Real historical observation counts supplied by GET /api/dashboard/stats."
            >
              <ActivityTimelineChart data={stats.activityOverTime} />
            </Card>
          )}

          {/* 6. Distribution (rendered when backend provides provider or protocol aggregated data) */}
          {distributionData && (
            <Card
              variant="surface"
              title={stats.providerDistribution ? "Provider Distribution" : "Network Protocol Distribution"}
              subtitle={
                stats.providerDistribution
                  ? "Aggregated traffic proportion across identified AI foundation vendors."
                  : "Observed network protocols distribution derived from processed traffic flows."
              }
            >
              <ProviderDistributionBars data={distributionData} />
            </Card>
          )}

          {/* 7. Recently Observed Endpoints (if supported by backend) */}
          {stats.recentlyObservedEndpoints && stats.recentlyObservedEndpoints.length > 0 && (
            <Card
              variant="surface"
              title="Recently Observed AI Endpoints"
              subtitle="Latest AI endpoints captured in network telemetry."
              action={
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/inventory')}
                  icon={<ExternalLink className="w-3 h-3" />}
                >
                  VIEW FULL INVENTORY
                </Button>
              }
            >
              <div className="border border-[#333330] overflow-x-auto">
                <table className="w-full border-collapse font-mono text-xs text-left">
                  <thead>
                    <tr className="bg-[#181818] border-b border-[#333330] text-[#FFCC00]">
                      <th className="py-2.5 px-3 uppercase">Endpoint</th>
                      <th className="py-2.5 px-3 uppercase">Provider</th>
                      <th className="py-2.5 px-3 uppercase">Observed At</th>
                      <th className="py-2.5 px-3 uppercase">Risk Level</th>
                      <th className="py-2.5 px-3 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#333330]">
                    {stats.recentlyObservedEndpoints.map((ep, idx) => (
                      <tr key={ep.id || idx} className="hover:bg-[#1E1E1C]">
                        <td className="py-2 px-3 text-[#FFCC00] font-bold">
                          {ep.endpoint}
                        </td>
                        <td className="py-2 px-3 text-[#F4F4F0]">
                          {ep.provider || 'Not available'}
                        </td>
                        <td className="py-2 px-3 text-[#9A9A91]">
                          {ep.observedAt || 'Not available'}
                        </td>
                        <td className="py-2 px-3">
                          {ep.riskLevel ? (
                            <Badge
                              size="sm"
                              variant={
                                ep.riskLevel === 'high' || ep.riskLevel === 'critical'
                                  ? 'danger'
                                  : ep.riskLevel === 'medium'
                                  ? 'warning'
                                  : 'default'
                              }
                            >
                              {ep.riskLevel.toUpperCase()}
                            </Badge>
                          ) : (
                            <span className="text-[#9A9A91]">Not available</span>
                          )}
                        </td>
                        <td className="py-2 px-3">
                          {ep.isApproved !== undefined ? (
                            ep.isApproved ? (
                              <Badge variant="success" size="sm">APPROVED</Badge>
                            ) : (
                              <Badge variant="danger" size="sm">SHADOW</Badge>
                            )
                          ) : (
                            <span className="text-[#9A9A91]">Not available</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* 8. Quick Links to Core Modules */}
      <div>
        <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#9A9A91] mb-3">
          Security Console Modules
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
          {/* Traffic Analysis Link */}
          <Card
            hoverable
            title="Traffic Analysis"
            subtitle="Deep packet & CSV/JSON ingestion"
            headerIcon={<Radio className="w-4 h-4 text-[#FFCC00]" />}
          >
            <p className="text-[#9A9A91] mb-4 leading-relaxed">
              Upload traffic captures (.csv, .json) via multipart/form-data to detect outbound AI calls.
            </p>
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => navigate('/traffic')}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              OPEN TRAFFIC ANALYSIS
            </Button>
          </Card>

          {/* AI Inventory Link */}
          <Card
            hoverable
            title="AI Inventory"
            subtitle="Provider & endpoint catalog"
            headerIcon={<Database className="w-4 h-4 text-[#FFCC00]" />}
          >
            <p className="text-[#9A9A91] mb-4 leading-relaxed">
              Explore discovered AI providers, unapproved shadow tools, and inspect endpoint details.
            </p>
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => navigate('/inventory')}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              VIEW AI INVENTORY
            </Button>
          </Card>

          {/* Risk Findings Link */}
          <Card
            hoverable
            title="Risk Findings"
            subtitle="Policy & data egress checks"
            headerIcon={<ShieldAlert className="w-4 h-4 text-[#FFCC00]" />}
          >
            <p className="text-[#9A9A91] mb-4 leading-relaxed">
              Review flagged policy violations, risk scores, and supporting evidence from network streams.
            </p>
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => navigate('/risks')}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              INSPECT RISK FINDINGS
            </Button>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
};
