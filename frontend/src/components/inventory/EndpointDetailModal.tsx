import React from 'react';
import { useEndpointDetail } from '../../hooks/useInventory';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { LoadingState } from '../common/LoadingState';
import { QueryErrorState } from '../common/QueryErrorState';
import {
  X,
  Database,
  Shield,
  CheckCircle2,
  XCircle,
  FileText,
  Network,
  Clock,
  Layers,
  Activity,
} from 'lucide-react';

export interface EndpointDetailModalProps {
  endpointId: string | null;
  onClose: () => void;
}

export const EndpointDetailModal: React.FC<EndpointDetailModalProps> = ({
  endpointId,
  onClose,
}) => {
  const {
    data: detail,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useEndpointDetail(endpointId || undefined);

  if (!endpointId) return null;

  const endpointAddress =
    detail?.hostname ||
    detail?.url ||
    detail?.endpointAddress ||
    detail?.domain ||
    'Not available';

  const endpointType =
    detail?.endpointType || detail?.category || detail?.type || 'Not available';

  const approvalLabel =
    detail?.isApproved !== undefined
      ? detail.isApproved
        ? 'APPROVED'
        : 'UNAPPROVED / SHADOW'
      : detail?.approvalStatus || detail?.status || 'Not available';

  const isApproved =
    detail?.isApproved === true ||
    (typeof detail?.approvalStatus === 'string' &&
      detail.approvalStatus.toLowerCase() === 'approved');

  const confidenceDisplay =
    detail?.confidence !== undefined
      ? `${(detail.confidence > 1 ? detail.confidence : detail.confidence * 100).toFixed(0)}%`
      : detail?.detectionConfidence !== undefined
      ? `${(detail.detectionConfidence > 1 ? detail.detectionConfidence : detail.detectionConfidence * 100).toFixed(0)}%`
      : 'Not available';

  const connectionCountDisplay =
    detail?.totalCalls !== undefined
      ? detail.totalCalls.toLocaleString()
      : detail?.requestCount !== undefined
      ? detail.requestCount.toLocaleString()
      : detail?.connectionCount !== undefined
      ? detail.connectionCount.toLocaleString()
      : detail?.observedRequests !== undefined
      ? detail.observedRequests.toLocaleString()
      : 'Not available';

  const dataTransferredDisplay =
    detail?.dataTransferred !== undefined
      ? typeof detail.dataTransferred === 'number'
        ? `${(detail.dataTransferred / (1024 * 1024)).toFixed(2)} MB`
        : String(detail.dataTransferred)
      : detail?.bytesTransferred !== undefined
      ? `${(detail.bytesTransferred / (1024 * 1024)).toFixed(2)} MB`
      : 'Not available';

  const evidenceItems = detail?.evidence
    ? Array.isArray(detail.evidence)
      ? detail.evidence
      : [String(detail.evidence)]
    : detail?.detectionEvidence
    ? Array.isArray(detail.detectionEvidence)
      ? detail.detectionEvidence
      : [String(detail.detectionEvidence)]
    : [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4 sm:p-6 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl bg-[#121212] border-2 border-[#333330] shadow-[6px_6px_0_#000000] p-6 sm:p-8 space-y-6 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b-2 border-[#333330]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#181818] border-2 border-[#FFCC00] shadow-[2px_2px_0_#735C00] flex items-center justify-center text-[#FFCC00]">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-[#9A9A91] uppercase tracking-wider">
                  GET /api/inventory/{endpointId}
                </span>
                {detail?.riskLevel && (
                  <Badge
                    size="sm"
                    variant={
                      detail.riskLevel === 'high' || detail.riskLevel === 'critical'
                        ? 'danger'
                        : detail.riskLevel === 'medium'
                        ? 'warning'
                        : 'default'
                    }
                  >
                    RISK: {detail.riskLevel.toUpperCase()}
                  </Badge>
                )}
              </div>
              <h2 className="font-mono text-base sm:text-lg font-bold text-[#F4F4F0] uppercase tracking-wide">
                {detail?.provider || 'Endpoint Details'}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 bg-[#181818] border border-[#333330] text-[#9A9A91] hover:text-[#F4F4F0] hover:border-[#FFCC00] cursor-pointer"
            aria-label="Close detail modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Loading State */}
        {isLoading && <LoadingState message={`FETCHING ENDPOINT #${endpointId} METADATA...`} />}

        {/* Error State */}
        {isError && (
          <QueryErrorState
            title={`Failed to Load Endpoint #${endpointId}`}
            error={error}
            onRetry={() => refetch()}
            isRetrying={isFetching}
          />
        )}

        {/* Detail Content */}
        {detail && !isLoading && !isError && (
          <div className="space-y-6 font-mono text-xs">
            {/* Core Identification Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">
                  Endpoint Hostname / Address
                </span>
                <span className="text-[#FFCC00] font-bold break-all">
                  {endpointAddress}
                </span>
              </div>

              <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">
                  Approval Status
                </span>
                <div className="flex items-center gap-2 mt-1">
                  {isApproved ? (
                    <Badge variant="success" size="sm" icon={<CheckCircle2 className="w-3 h-3 text-[#00E575]" />}>
                      {approvalLabel}
                    </Badge>
                  ) : (
                    <Badge variant="danger" size="sm" icon={<XCircle className="w-3 h-3 text-[#FF6B6B]" />}>
                      {approvalLabel}
                    </Badge>
                  )}
                </div>
              </div>

              <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">
                  Endpoint Type / Category
                </span>
                <span className="text-[#F4F4F0]">{endpointType}</span>
              </div>

              <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">
                  Detection Confidence
                </span>
                <span className="text-[#00E575] font-bold">{confidenceDisplay}</span>
              </div>

              <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">
                  Observed Requests / Connections
                </span>
                <span className="text-[#F4F4F0] font-bold">{connectionCountDisplay}</span>
              </div>

              <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">
                  Data Transferred
                </span>
                <span className="text-[#F4F4F0] font-bold">{dataTransferredDisplay}</span>
              </div>

              <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                <span className="text-[#9A9A91] text-[10px] uppercase block mb-1 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> First Seen
                </span>
                <span className="text-[#9A9A91]">{detail.firstSeenAt || 'Not available'}</span>
              </div>

              <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                <span className="text-[#9A9A91] text-[10px] uppercase block mb-1 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Last Seen
                </span>
                <span className="text-[#9A9A91]">{detail.lastSeenAt || 'Not available'}</span>
              </div>
            </div>

            {/* Risk Score & Investigation */}
            {(detail.riskScore !== undefined || detail.investigationStatus) && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {detail.riskScore !== undefined && (
                  <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                    <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">
                      Official Risk Score
                    </span>
                    <span className="text-base font-bold text-[#FFCC00]">
                      {String(detail.riskScore)}
                    </span>
                  </div>
                )}
                {detail.investigationStatus && (
                  <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                    <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">
                      Investigation Status
                    </span>
                    <Badge variant="muted">{detail.investigationStatus}</Badge>
                  </div>
                )}
              </div>
            )}

            {/* Models & Subnets */}
            {(detail.observedModels || detail.allowedSubnets) && (
              <div className="space-y-3">
                {detail.observedModels && detail.observedModels.length > 0 && (
                  <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                    <span className="text-[#9A9A91] text-[10px] uppercase block mb-1.5 flex items-center gap-1">
                      <Layers className="w-3 h-3 text-[#FFCC00]" /> Observed Models
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {detail.observedModels.map((m, idx) => (
                        <Badge key={idx} variant="muted" size="sm">
                          {m}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {detail.allowedSubnets && detail.allowedSubnets.length > 0 && (
                  <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                    <span className="text-[#9A9A91] text-[10px] uppercase block mb-1.5 flex items-center gap-1">
                      <Network className="w-3 h-3 text-[#FFCC00]" /> Allowed Subnets
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {detail.allowedSubnets.map((sub, idx) => (
                        <span key={idx} className="bg-[#181818] px-2 py-0.5 border border-[#333330] text-[11px]">
                          {sub}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Explanation & Detection Evidence */}
            <div className="space-y-3">
              {(detail.explanation || detail.riskExplanation) && (
                <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                  <span className="text-[#9A9A91] text-[10px] uppercase block mb-1 flex items-center gap-1">
                    <FileText className="w-3 h-3 text-[#FFCC00]" /> Explanation
                  </span>
                  <p className="text-[#F4F4F0] leading-relaxed">
                    {detail.explanation || detail.riskExplanation}
                  </p>
                </div>
              )}

              {evidenceItems.length > 0 && (
                <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                  <span className="text-[#9A9A91] text-[10px] uppercase block mb-1.5 flex items-center gap-1">
                    <Shield className="w-3 h-3 text-[#FFCC00]" /> Supporting Detection Evidence
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-[#9A9A91]">
                    {evidenceItems.map((ev, idx) => (
                      <li key={idx} className="text-[#F4F4F0]">
                        {ev}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {detail.detectionSignatures && detail.detectionSignatures.length > 0 && (
                <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                  <span className="text-[#9A9A91] text-[10px] uppercase block mb-1.5 flex items-center gap-1">
                    <Activity className="w-3 h-3 text-[#FFCC00]" /> Detection Signatures
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {detail.detectionSignatures.map((sig, idx) => (
                      <span key={idx} className="bg-[#181818] text-[#FFCC00] px-2 py-0.5 border border-[#333330] text-[10px]">
                        {sig}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {detail.notes && (
                <div className="bg-[#0D0D0D] p-3 border border-[#333330]">
                  <span className="text-[#9A9A91] text-[10px] uppercase block mb-1">Notes</span>
                  <p className="text-[#9A9A91] leading-relaxed">{detail.notes}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t border-[#333330]">
          <Button variant="secondary" size="sm" onClick={onClose}>
            CLOSE PANEL
          </Button>
        </div>
      </div>
    </div>
  );
};
