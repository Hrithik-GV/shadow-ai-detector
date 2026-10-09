import React from 'react';
import { PageContainer } from '../components/common/PageContainer';
import { Table, type Column } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { RefreshCw, Filter } from 'lucide-react';
import type { NetworkTrafficEvent } from '../types';

export const TrafficPage: React.FC = () => {
  // Empty array - strictly no fabricated metrics or fake data
  const trafficData: NetworkTrafficEvent[] = [];

  const columns: Column<NetworkTrafficEvent>[] = [
    {
      key: 'timestamp',
      header: 'TIMESTAMP',
      width: '180px',
      render: (item) => <span className="text-[#9A9A91]">{item.timestamp}</span>,
    },
    {
      key: 'sourceIp',
      header: 'SOURCE IP',
      width: '140px',
      render: (item) => <span className="text-[#F4F4F0] font-bold">{item.sourceIp}</span>,
    },
    {
      key: 'destinationHost',
      header: 'DESTINATION HOST',
      render: (item) => <span className="text-[#FFCC00]">{item.destinationHost}</span>,
    },
    {
      key: 'protocol',
      header: 'PROTOCOL',
      width: '100px',
      render: (item) => <Badge variant="muted">{item.protocol}</Badge>,
    },
    {
      key: 'riskLevel',
      header: 'RISK LEVEL',
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
      title="Traffic Analysis"
      description="Inspect network telemetry, outbound AI payload streams, and unknown API proxy connections."
      badge={<Badge variant="accent">STREAM ACTIVE</Badge>}
      actions={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={<Filter className="w-3.5 h-3.5" />}
            disabled
          >
            FILTER
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH
          </Button>
        </div>
      }
    >
      <Table
        columns={columns}
        data={trafficData}
        keyExtractor={(item) => item.id}
        emptyTitle="No Traffic Telemetry Recorded"
        emptyDescription="No network traffic streams detected. Awaiting ingestion from mirrored network sensor, proxy tap, or endpoint collector."
      />
    </PageContainer>
  );
};
