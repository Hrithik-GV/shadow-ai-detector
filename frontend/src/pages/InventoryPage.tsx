import React, { useState, useMemo } from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { EndpointDetailModal } from '../components/inventory/EndpointDetailModal';
import { useInventory } from '../hooks/useInventory';
import {
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Database,
} from 'lucide-react';
import type { EndpointInventoryItem } from '../types';

export const InventoryPage: React.FC = () => {
  const { data: inventoryData, isLoading, isError, error, refetch, isFetching } = useInventory();

  // Search & Filter States
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [approvalFilter, setApprovalFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedEndpointId, setSelectedEndpointId] = useState<string | null>(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 10;

  // Extract distinct endpoint types from real backend response
  const availableTypes = useMemo(() => {
    if (!inventoryData) return [];
    const set = new Set<string>();
    inventoryData.forEach((item) => {
      const t = item.endpointType || item.category || item.type;
      if (t) set.add(t);
    });
    return Array.from(set);
  }, [inventoryData]);

  // Safe client-side filtering over returned records
  const filteredInventory = useMemo(() => {
    if (!inventoryData) return [];

    return inventoryData.filter((item: EndpointInventoryItem) => {
      const provider = (item.provider || '').toLowerCase();
      const hostname = (
        item.hostname ||
        item.url ||
        item.endpointAddress ||
        item.domain ||
        ''
      ).toLowerCase();
      const search = searchTerm.toLowerCase();

      const matchesSearch =
        searchTerm === '' || provider.includes(search) || hostname.includes(search);

      // Approval filter
      const isItemApproved =
        item.isApproved === true ||
        (typeof item.approvalStatus === 'string' &&
          item.approvalStatus.toLowerCase() === 'approved');

      const matchesApproval =
        approvalFilter === 'all' ||
        (approvalFilter === 'approved' && isItemApproved) ||
        (approvalFilter === 'unapproved' && !isItemApproved);

      // Risk level filter
      const risk = (item.riskLevel || '').toLowerCase();
      const matchesRisk = riskFilter === 'all' || risk === riskFilter.toLowerCase();

      // Endpoint type filter
      const itemType = (item.endpointType || item.category || item.type || '').toLowerCase();
      const matchesType = typeFilter === 'all' || itemType === typeFilter.toLowerCase();

      return matchesSearch && matchesApproval && matchesRisk && matchesType;
    });
  }, [inventoryData, searchTerm, approvalFilter, riskFilter, typeFilter]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredInventory.length / pageSize));
  const paginatedInventory = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredInventory.slice(start, start + pageSize);
  }, [filteredInventory, currentPage, pageSize]);

  return (
    <PageContainer
      title="AI Inventory"
      description="Registry of discovered generative AI foundation providers, web portals, shadow endpoints, and tool subscriptions."
      badge={
        <Badge variant={inventoryData && inventoryData.length > 0 ? 'accent' : 'default'}>
          {inventoryData ? `${inventoryData.length} REGISTERED` : 'GET /api/inventory'}
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
          REFRESH INVENTORY
        </Button>
      }
    >
      {/* Loading State */}
      {isLoading && <LoadingState message="FETCHING ENDPOINT INVENTORY FROM GET /api/inventory..." />}

      {/* Error State */}
      {isError && (
        <QueryErrorState
          title="Inventory API Error"
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
                placeholder="SEARCH PROVIDER OR HOSTNAME..."
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

              <div className="flex items-center gap-1.5">
                <span className="text-[#9A9A91] text-[11px] uppercase">Risk:</span>
                <select
                  value={riskFilter}
                  onChange={(e) => {
                    setRiskFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="bg-[#171716] border border-[#333330] px-2.5 py-1.5 text-[#F4F4F0] font-mono text-xs focus:outline-none focus:border-[#FFCC00]"
                >
                  <option value="all">ALL RISKS</option>
                  <option value="critical">CRITICAL</option>
                  <option value="high">HIGH</option>
                  <option value="medium">MEDIUM</option>
                  <option value="low">LOW</option>
                </select>
              </div>

              {availableTypes.length > 0 && (
                <div className="flex items-center gap-1.5">
                  <span className="text-[#9A9A91] text-[11px] uppercase">Type:</span>
                  <select
                    value={typeFilter}
                    onChange={(e) => {
                      setTypeFilter(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="bg-[#171716] border border-[#333330] px-2.5 py-1.5 text-[#F4F4F0] font-mono text-xs focus:outline-none focus:border-[#FFCC00]"
                  >
                    <option value="all">ALL TYPES</option>
                    {availableTypes.map((t) => (
                      <option key={t} value={t}>
                        {t.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* Table / Empty State */}
          {filteredInventory.length === 0 ? (
            <EmptyState
              title={
                inventoryData?.length === 0
                  ? 'AI Provider Inventory Is Unpopulated'
                  : 'No Matching Endpoints Found'
              }
              description={
                inventoryData?.length === 0
                  ? 'No endpoint records were returned by GET /api/inventory. Connect a network discovery agent or run a traffic scan to catalog endpoints.'
                  : 'No endpoint records match the current search term and filters. Try clearing your filters.'
              }
              statusLabel={inventoryData?.length === 0 ? 'EMPTY INVENTORY' : 'NO RESULTS'}
              icon={<Database className="w-7 h-7" />}
              action={
                inventoryData && inventoryData.length > 0 ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSearchTerm('');
                      setApprovalFilter('all');
                      setRiskFilter('all');
                      setTypeFilter('all');
                      setCurrentPage(1);
                    }}
                  >
                    RESET FILTERS
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="border-2 border-[#333330] bg-[#171716] shadow-[4px_4px_0_#000000] overflow-x-auto">
              <table className="w-full border-collapse font-mono text-xs text-left">
                <thead>
                  <tr className="bg-[#181818] border-b-2 border-[#333330] text-[#FFCC00]">
                    <th className="py-3 px-3 uppercase tracking-wider">Provider</th>
                    <th className="py-3 px-3 uppercase tracking-wider">Endpoint Hostname / Address</th>
                    <th className="py-3 px-3 uppercase tracking-wider">Type</th>
                    <th className="py-3 px-3 uppercase tracking-wider">Approval</th>
                    <th className="py-3 px-3 uppercase tracking-wider">Confidence</th>
                    <th className="py-3 px-3 uppercase tracking-wider">Requests</th>
                    <th className="py-3 px-3 uppercase tracking-wider">Data Transferred</th>
                    <th className="py-3 px-3 uppercase tracking-wider">First Seen</th>
                    <th className="py-3 px-3 uppercase tracking-wider">Last Seen</th>
                    <th className="py-3 px-3 uppercase tracking-wider">Risk</th>
                    <th className="py-3 px-3 uppercase tracking-wider text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#333330]">
                  {paginatedInventory.map((item) => {
                    const hostnameDisplay =
                      item.hostname ||
                      item.url ||
                      item.endpointAddress ||
                      item.domain ||
                      'Not available';

                    const typeDisplay =
                      item.endpointType || item.category || item.type || 'Not available';

                    const isItemApproved =
                      item.isApproved === true ||
                      (typeof item.approvalStatus === 'string' &&
                        item.approvalStatus.toLowerCase() === 'approved');

                    const confidenceDisplay =
                      item.confidence !== undefined
                        ? `${(item.confidence > 1 ? item.confidence : item.confidence * 100).toFixed(0)}%`
                        : item.detectionConfidence !== undefined
                        ? `${(item.detectionConfidence > 1 ? item.detectionConfidence : item.detectionConfidence * 100).toFixed(0)}%`
                        : 'Not available';

                    const requestCountDisplay =
                      item.totalCalls !== undefined
                        ? item.totalCalls.toLocaleString()
                        : item.requestCount !== undefined
                        ? item.requestCount.toLocaleString()
                        : item.connectionCount !== undefined
                        ? item.connectionCount.toLocaleString()
                        : item.observedRequests !== undefined
                        ? item.observedRequests.toLocaleString()
                        : 'Not available';

                    const dataTransferredDisplay =
                      item.dataTransferred !== undefined
                        ? typeof item.dataTransferred === 'number'
                          ? `${(item.dataTransferred / (1024 * 1024)).toFixed(2)} MB`
                          : String(item.dataTransferred)
                        : item.bytesTransferred !== undefined
                        ? `${(item.bytesTransferred / (1024 * 1024)).toFixed(2)} MB`
                        : 'Not available';

                    return (
                      <tr
                        key={item.id}
                        className="hover:bg-[#1E1E1C] transition-colors cursor-pointer group"
                        onClick={() => setSelectedEndpointId(item.id)}
                      >
                        <td className="py-2.5 px-3 font-bold text-[#F4F4F0] whitespace-nowrap">
                          {item.provider || 'Not available'}
                        </td>
                        <td className="py-2.5 px-3 text-[#FFCC00] max-w-[200px] truncate" title={hostnameDisplay}>
                          {hostnameDisplay}
                        </td>
                        <td className="py-2.5 px-3">
                          {typeDisplay !== 'Not available' ? (
                            <Badge variant="muted" size="sm">{typeDisplay}</Badge>
                          ) : (
                            <span className="text-[#9A9A91]">Not available</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 whitespace-nowrap">
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
                        <td className="py-2.5 px-3 text-[#00E575] font-bold">
                          {confidenceDisplay}
                        </td>
                        <td className="py-2.5 px-3 text-[#F4F4F0]">
                          {requestCountDisplay}
                        </td>
                        <td className="py-2.5 px-3 text-[#9A9A91]">
                          {dataTransferredDisplay}
                        </td>
                        <td className="py-2.5 px-3 text-[#9A9A91] whitespace-nowrap">
                          {item.firstSeenAt || 'Not available'}
                        </td>
                        <td className="py-2.5 px-3 text-[#9A9A91] whitespace-nowrap">
                          {item.lastSeenAt || 'Not available'}
                        </td>
                        <td className="py-2.5 px-3 whitespace-nowrap">
                          {item.riskLevel ? (
                            <Badge
                              size="sm"
                              variant={
                                item.riskLevel === 'high' || item.riskLevel === 'critical'
                                  ? 'danger'
                                  : item.riskLevel === 'medium'
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
                        <td className="py-2.5 px-3 text-right whitespace-nowrap">
                          <Button
                            variant="secondary"
                            size="sm"
                            icon={<ExternalLink className="w-3 h-3" />}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedEndpointId(item.id);
                            }}
                          >
                            DETAILS
                          </Button>
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
                  {Math.min(currentPage * pageSize, filteredInventory.length)} of{' '}
                  {filteredInventory.length} endpoints
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
          )}
        </div>
      )}

      {/* Detail Drawer Modal (GET /api/inventory/{endpoint_id}) */}
      <EndpointDetailModal
        endpointId={selectedEndpointId}
        onClose={() => setSelectedEndpointId(null)}
      />
    </PageContainer>
  );
};
