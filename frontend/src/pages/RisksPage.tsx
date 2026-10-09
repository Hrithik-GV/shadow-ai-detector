import React, { useState, useMemo } from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { useRisks } from '../hooks/useRisks';
import {
  RefreshCw,
  Search,
  Filter,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { RiskAssessment } from '../types';

export const RisksPage: React.FC = () => {
  const { data: riskData, isLoading, isError, error, refetch, isFetching } = useRisks();

  // Search & Filter States
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [approvalFilter, setApprovalFilter] = useState<string>('all');

  // Pagination State
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 10;

  // Safe client-side filtering over returned records
  const filteredRisks = useMemo(() => {
    if (!riskData) return [];

    return riskData.filter((item: RiskAssessment) => {
      const provider = (item.provider || '').toLowerCase();
      const endpoint = (item.endpoint || item.target || item.endpointHostname || '').toLowerCase();
      const search = searchTerm.toLowerCase();

      const matchesSearch =
        searchTerm === '' || provider.includes(search) || endpoint.includes(search);

      // Risk level filter (strictly backend label)
      const level = (item.riskLevel || '').toLowerCase();
      const matchesRisk = riskFilter === 'all' || level === riskFilter.toLowerCase();

      // Approval filter
      const isApproved =
        item.isApproved === true ||
        (typeof item.approvalStatus === 'string' &&
          item.approvalStatus.toLowerCase() === 'approved');

      const matchesApproval =
        approvalFilter === 'all' ||
        (approvalFilter === 'approved' && isApproved) ||
        (approvalFilter === 'unapproved' && !isApproved);

      return matchesSearch && matchesRisk && matchesApproval;
    });
  }, [riskData, searchTerm, riskFilter, approvalFilter]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredRisks.length / pageSize));
  const paginatedRisks = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRisks.slice(start, start + pageSize);
  }, [filteredRisks, currentPage, pageSize]);

  return (
    <PageContainer
      title="Risk Findings"
      description="Security evaluations, data egress alerts, and unapproved shadow AI classifications derived from endpoint telemetry."
      badge={
        <Badge
          variant={riskData && riskData.length > 0 ? 'danger' : 'default'}
        >
          {riskData ? `${riskData.length} EVALUATED` : 'API CONTRACT'}
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
          REFRESH FINDINGS
        </Button>
      }
    >
      {/* Loading State */}
      {isLoading && <LoadingState message="EVALUATING RISK FINDINGS FROM BACKEND CONTRACT..." />}

      {/* Error State */}
      {isError && (
        <QueryErrorState
          title="Risk Engine API Error"
          error={error}
          onRetry={() => refetch()}
          isRetrying={isFetching}
        />
      )}

      {/* Main Content Area */}
      {!isLoading && !isError && (
        <div className="space-y-4">
          {/* Search and Filters Toolbar */}
          <div className="bg-[#121212] border-2 border-[#333330] p-4 shadow-[3px_3px_0_#000000] flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3 font-mono text-xs">
            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#9A9A91]" />
              <input
                type="text"
                placeholder="SEARCH PROVIDER OR ENDPOINT..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full bg-[#171716] border border-[#333330] pl-9 pr-3 py-2 text-[#F4F4F0] font-mono text-xs focus:outline-none focus:border-[#FFCC00] placeholder:text-[#9A9A91]"
              />
            </div>

            {/* Filter Dropdowns */}
            <div className="flex flex-wrap items-center gap-2.5">
              <div className="flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-[#9A9A91]" />
                <span className="text-[#9A9A91] text-[11px] uppercase">Risk Level:</span>
                <select
                  value={riskFilter}
                  onChange={(e) => {
                    setRiskFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="bg-[#171716] border border-[#333330] px-2.5 py-1.5 text-[#F4F4F0] font-mono text-xs focus:outline-none focus:border-[#FFCC00]"
                >
                  <option value="all">ALL SEVERITIES</option>
                  <option value="critical">CRITICAL</option>
                  <option value="high">HIGH</option>
                  <option value="medium">MEDIUM</option>
                  <option value="low">LOW</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-[#9A9A91] text-[11px] uppercase">Approval:</span>
                <select
                  value={approvalFilter}
                  onChange={(e) => {
                    setApprovalFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="bg-[#171716] border border-[#333330] px-2.5 py-1.5 text-[#F4F4F0] font-mono text-xs focus:outline-none focus:border-[#FFCC00]"
                >
                  <option value="all">ALL STATUSES</option>
                  <option value="approved">APPROVED ONLY</option>
                  <option value="unapproved">UNAPPROVED / SHADOW</option>
                </select>
              </div>
            </div>
          </div>

          {/* Table / Empty State */}
          {filteredRisks.length === 0 ? (
            <EmptyState
              title={
                riskData?.length === 0
                  ? 'No Risk Findings Flagged'
                  : 'No Matching Risk Findings'
              }
              description={
                riskData?.length === 0
                  ? 'No endpoint risk findings or policy violations returned by the backend. Risk classifications will appear when network telemetry is assessed.'
                  : 'No findings match the current search term and filters. Try clearing your filters.'
              }
              statusLabel={riskData?.length === 0 ? 'ZERO VIOLATIONS' : 'NO RESULTS'}
              icon={<ShieldAlert className="w-7 h-7" />}
              action={
                riskData && riskData.length > 0 ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSearchTerm('');
                      setRiskFilter('all');
                      setApprovalFilter('all');
                      setCurrentPage(1);
                    }}
                  >
                    RESET FILTERS
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="space-y-4">
              {/* Detailed Findings List */}
              <div className="border-2 border-[#333330] bg-[#171716] shadow-[4px_4px_0_#000000] overflow-x-auto">
                <table className="w-full border-collapse font-mono text-xs text-left">
                  <thead>
                    <tr className="bg-[#181818] border-b-2 border-[#333330] text-[#FFCC00]">
                      <th className="py-3 px-3 uppercase tracking-wider">Risk Level</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Risk Score</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Provider</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Endpoint Address</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Approval</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Finding Reasons</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Evidence</th>
                      <th className="py-3 px-3 uppercase tracking-wider">First Seen</th>
                      <th className="py-3 px-3 uppercase tracking-wider">Investigation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#333330]">
                    {paginatedRisks.map((item) => {
                      const endpointDisplay =
                        item.endpoint ||
                        item.target ||
                        item.endpointHostname ||
                        'Not available';

                      const isItemApproved =
                        item.isApproved === true ||
                        (typeof item.approvalStatus === 'string' &&
                          item.approvalStatus.toLowerCase() === 'approved');

                      const reasonsDisplay = item.reasons
                        ? Array.isArray(item.reasons)
                          ? item.reasons.join('; ')
                          : String(item.reasons)
                        : item.description || 'Not available';

                      const evidenceDisplay = item.evidence
                        ? Array.isArray(item.evidence)
                          ? item.evidence.join(', ')
                          : String(item.evidence)
                        : 'Not available';

                      const riskScoreDisplay =
                        item.riskScore !== undefined
                          ? String(item.riskScore)
                          : 'Not available';

                      return (
                        <tr
                          key={item.id}
                          className="hover:bg-[#1E1E1C] transition-colors"
                        >
                          <td className="py-3 px-3 whitespace-nowrap">
                            {item.riskLevel ? (
                              <Badge
                                size="sm"
                                variant={
                                  item.riskLevel.toLowerCase() === 'high' ||
                                  item.riskLevel.toLowerCase() === 'critical'
                                    ? 'danger'
                                    : item.riskLevel.toLowerCase() === 'medium'
                                    ? 'warning'
                                    : 'default'
                                }
                              >
                                {item.riskLevel.toUpperCase()}
                              </Badge>
                            ) : (
                              <span className="text-[#9A9A91]">Not available</span>
                            )}
                          </td>
                          <td className="py-3 px-3 font-bold text-[#FFCC00] whitespace-nowrap">
                            {riskScoreDisplay}
                          </td>
                          <td className="py-3 px-3 font-bold text-[#F4F4F0] whitespace-nowrap">
                            {item.provider || 'Not available'}
                          </td>
                          <td className="py-3 px-3 text-[#FFCC00] max-w-[180px] truncate" title={endpointDisplay}>
                            {endpointDisplay}
                          </td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            {item.isApproved !== undefined || item.approvalStatus ? (
                              isItemApproved ? (
                                <Badge variant="success" size="sm" icon={<CheckCircle2 className="w-3 h-3 text-[#00E575]" />}>
                                  APPROVED
                                </Badge>
                              ) : (
                                <Badge variant="danger" size="sm" icon={<XCircle className="w-3 h-3 text-[#FF6B6B]" />}>
                                  SHADOW / UNAPPROVED
                                </Badge>
                              )
                            ) : (
                              <span className="text-[#9A9A91]">Not available</span>
                            )}
                          </td>
                          <td className="py-3 px-3 text-[#F4F4F0] max-w-[240px] truncate" title={reasonsDisplay}>
                            {reasonsDisplay}
                          </td>
                          <td className="py-3 px-3 text-[#9A9A91] max-w-[180px] truncate text-[11px]" title={evidenceDisplay}>
                            {evidenceDisplay}
                          </td>
                          <td className="py-3 px-3 text-[#9A9A91] whitespace-nowrap">
                            {item.firstSeenAt || 'Not available'}
                          </td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            {item.investigationStatus ? (
                              <Badge variant="muted" size="sm">
                                {item.investigationStatus.toUpperCase()}
                              </Badge>
                            ) : item.status ? (
                              <Badge variant="muted" size="sm">
                                {item.status.toUpperCase()}
                              </Badge>
                            ) : (
                              <span className="text-[#9A9A91]">Not available</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                {/* Pagination Bar */}
                <div className="p-3 bg-[#181818] border-t border-[#333330] flex items-center justify-between font-mono text-xs">
                  <div className="text-[#9A9A91]">
                    Showing {(currentPage - 1) * pageSize + 1} to{' '}
                    {Math.min(currentPage * pageSize, filteredRisks.length)} of{' '}
                    {filteredRisks.length} findings
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      icon={<ChevronLeft className="w-3.5 h-3.5" />}
                    >
                      PREV
                    </Button>
                    <span className="px-2 text-[#F4F4F0]">
                      {currentPage} / {totalPages}
                    </span>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      icon={<ChevronRight className="w-3.5 h-3.5" />}
                    >
                      NEXT
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </PageContainer>
  );
};
