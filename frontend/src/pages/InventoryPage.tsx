import React from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Table, type Column } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { LoadingState } from '../components/common/LoadingState';
import { useInventory } from '../hooks/useInventory';
import { RefreshCw, CheckCircle2, XCircle } from 'lucide-react';
import type { EndpointInventoryItem } from '../types';

export const InventoryPage: React.FC = () => {
  const { data: inventoryData, isLoading, isError, error, refetch, isFetching } = useInventory();

  const columns: Column<EndpointInventoryItem>[] = [
    {
      key: 'provider',
      header: 'PROVIDER',
      render: (item) => <span className="text-[#F4F4F0] font-bold">{item.provider}</span>,
    },
    {
      key: 'domain',
      header: 'DOMAIN',
      render: (item) => <span className="text-[#FFCC00]">{item.domain}</span>,
    },
    {
      key: 'url',
      header: 'ENDPOINT URL',
      render: (item) => (
        <span className="text-[#9A9A91] truncate max-w-[200px] block" title={item.url}>
          {item.url}
        </span>
      ),
    },
    {
      key: 'category',
      header: 'CATEGORY',
      render: (item) => <Badge variant="muted">{item.category}</Badge>,
    },
    {
      key: 'isApproved',
      header: 'APPROVAL',
      width: '120px',
      render: (item) =>
        item.isApproved ? (
          <Badge variant="success" size="sm" icon={<CheckCircle2 className="w-3 h-3 text-[#00E575]" />}>
            APPROVED
          </Badge>
        ) : (
          <Badge variant="danger" size="sm" icon={<XCircle className="w-3 h-3 text-[#FF6B6B]" />}>
            SHADOW / UNAPPROVED
          </Badge>
        ),
    },
    {
      key: 'riskLevel',
      header: 'RISK SCORE',
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
  ];

  return (
    <PageContainer
      title="AI Inventory"
      description="Catalog of discovered generative AI providers, models, web interfaces, and shadow API endpoints."
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
      {isLoading && <LoadingState message="FETCHING ENDPOINT INVENTORY FROM BACKEND..." />}

      {isError && (
        <QueryErrorState
          title="Inventory API Error"
          error={error}
          onRetry={() => refetch()}
          isRetrying={isFetching}
        />
      )}

      {!isLoading && !isError && (
        <Table
          columns={columns}
          data={inventoryData || []}
          keyExtractor={(item) => item.id}
          emptyTitle="AI Provider Inventory Is Unpopulated"
          emptyDescription="No AI service endpoints have been cataloged yet. Ingestion scans will populate detected providers here automatically."
        />
      )}
    </PageContainer>
  );
};
