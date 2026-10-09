import React from 'react';
import { usePolicyAuditLogs } from '../../hooks/usePolicies';
import { Badge } from '../common/Badge';
import { LoadingState } from '../common/LoadingState';
import { QueryErrorState } from '../common/QueryErrorState';
import { EmptyState } from '../common/EmptyState';
import { X, History, UserCheck } from 'lucide-react';

export interface PolicyAuditLogDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PolicyAuditLogDrawer: React.FC<PolicyAuditLogDrawerProps> = ({
  isOpen,
  onClose,
}) => {
  const { data: logs, isLoading, isError, error, refetch } = usePolicyAuditLogs(50);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-[#000000]/80 backdrop-blur-xs flex items-center justify-end">
      <div className="w-full max-w-2xl h-full border-l-2 border-[#333330] bg-[#121212] shadow-[-8px_0_0_#000000] flex flex-col font-mono text-xs">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b-2 border-[#333330] bg-[#181818]">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-[#FFCC00]" />
            <h3 className="font-bold text-[#F4F4F0] uppercase tracking-wider text-sm">
              Policy Governance Audit Trail
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-[#9A9A91] hover:text-[#F4F4F0] p-1 border border-transparent hover:border-[#333330] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 flex-1 overflow-y-auto space-y-3">
          {isLoading ? (
            <LoadingState message="Loading policy audit history..." />
          ) : isError ? (
            <QueryErrorState error={error} onRetry={() => refetch()} />
          ) : !logs || logs.length === 0 ? (
            <EmptyState
              title="No audit entries"
              description="Administrative modifications and status updates will be logged here."
            />
          ) : (
            logs.map((log) => {
              const actionVariant =
                log.action === 'create'
                  ? 'success'
                  : log.action === 'disable' || log.action === 'delete'
                  ? 'danger'
                  : 'warning';

              const formattedDate = new Date(log.timestamp).toLocaleString();

              return (
                <div
                  key={log.id}
                  className="p-3 bg-[#0D0D0D] border border-[#333330] space-y-2 hover:border-[#666660] transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant={actionVariant} size="sm">
                        {log.action}
                      </Badge>
                      <span className="font-bold text-[#F4F4F0]">
                        {log.providerName || log.provider_name}
                      </span>
                    </div>
                    <span className="text-[10px] text-[#9A9A91]">{formattedDate}</span>
                  </div>

                  {log.details && (
                    <p className="text-[11px] text-[#CACAC4] pl-2 border-l-2 border-[#333330]">
                      {log.details}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-[#9A9A91] pt-1 border-t border-[#222220]">
                    <span className="flex items-center gap-1">
                      <UserCheck className="w-3 h-3 text-[#FFCC00]" />
                      Performed by: <span className="text-[#F4F4F0]">{log.performedBy || log.performed_by}</span>
                    </span>
                    {log.policyId && (
                      <span className="font-mono text-[9px] text-[#666660]">
                        ID: {String(log.policyId).slice(0, 8)}...
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
