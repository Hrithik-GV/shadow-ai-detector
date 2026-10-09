import React from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Table, type Column } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { useRisks } from '../hooks/useRisks';
import { RefreshCw } from 'lucide-react';
import type { RiskAssessment } from '../types';

export const RisksPage: React.FC = () => {
  const { data: riskData, isLoading, isError, error, refetch, isFetching } = useRisks();

  const columns: Column<RiskAssessment>[] = [
    {
      key: 'id',
      header: 'FINDING ID',
      width: '120px',
      render: (item) => <span className="text-[#FFCC00] font-bold">{item.id}</span>,
    },
    {
      key: 'target',
      header: 'TARGET ENDPOINT',
      render: (item) => <span className="text-[#F4F4F0]">{item.target}</span>,
    },
    {
      key: 'policyRule',
      header: 'POLICY RULE',
      render: (item) => <span className="text-[#9A9A91]">{item.policyRule}</span>,
    },
    {
      key: 'riskLevel',
      header: 'SEVERITY',
      width: '120px',
      render: (item) => (
        <Badge
          variant={
            item.riskLevel === 'high' || item.riskLevel === 'critical'
              ? 'danger'
              : item.riskLevel === 'medium'
              ? 'warning'
              : 'default'
          }
        >
          {item.riskLevel}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'STATUS',
      width: '120px',
      render: (item) => <Badge variant="muted">{item.status}</Badge>,
    },
    {
      key: 'assessedAt',
      header: 'DETECTED AT',
      render: (item) => <span className="text-[#9A9A91]">{item.assessedAt}</span>,
    },
  ];

  return (
    <PageContainer
      title="Risk Findings"
      description="Security policy violations, sensitive data egress alerts, and unapproved shadow AI classifications."
      badge={
        <Badge variant={riskData && riskData.length > 0 ? 'danger' : 'default'}>
          {riskData ? `${riskData.length} VIOLATIONS` : 'GET /api/risks'}
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
      {isLoading && <LoadingState message="EVALUATING RISK FINDINGS FROM BACKEND..." />}

      {isError && (
        <QueryErrorState
          title="Risk Engine API Error"
          error={error}
          onRetry={() => refetch()}
          isRetrying={isFetching}
        />
      )}

      {!isLoading && !isError && (
        <Table
          columns={columns}
          data={riskData || []}
          keyExtractor={(item) => item.id}
          emptyTitle="No Risk Classifications Flagged"
          emptyDescription="Risk classifications, vulnerability tags, and regulatory violation alerts will be listed once traffic is classified by the risk engine."
        />
      )}
    </PageContainer>
  );
};
