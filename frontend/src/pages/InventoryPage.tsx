import React from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Table, type Column } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Search, RefreshCw } from 'lucide-react';
import type { AIProvider } from '../types';

export const InventoryPage: React.FC = () => {
  // Empty array - strictly no fabricated metrics or fake data
  const inventoryData: AIProvider[] = [];

  const columns: Column<AIProvider>[] = [
    {
      key: 'name',
      header: 'PROVIDER / TOOL',
      render: (item) => <span className="text-[#F4F4F0] font-bold">{item.name}</span>,
    },
    {
      key: 'domain',
      header: 'DOMAIN',
      render: (item) => <span className="text-[#FFCC00]">{item.domain}</span>,
    },
    {
      key: 'category',
      header: 'CATEGORY',
      render: (item) => <Badge variant="muted">{item.category}</Badge>,
    },
    {
      key: 'riskLevel',
      header: 'RISK SCORE',
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
          {item.riskLevel || 'UNASSESSED'}
        </Badge>
      ),
    },
    {
      key: 'firstSeenAt',
      header: 'FIRST SEEN',
      render: (item) => <span className="text-[#9A9A91]">{item.firstSeenAt || '-'}</span>,
    },
  ];

  return (
    <PageContainer
      title="AI Inventory"
      description="Catalog of discovered generative AI providers, models, web interfaces, and shadow API endpoints."
      badge={<Badge variant="default">0 REGISTERED</Badge>}
      actions={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={<Search className="w-3.5 h-3.5" />}
            disabled
          >
            SEARCH
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            DISCOVERY SCAN
          </Button>
        </div>
      }
    >
      <Table
        columns={columns}
        data={inventoryData}
        keyExtractor={(item) => item.id}
        emptyTitle="AI Provider Inventory Is Unpopulated"
        emptyDescription="Detected AI providers, API endpoints, and unauthorized tool accounts will appear here once discovered by deep inspection rules."
      />
    </PageContainer>
  );
};
