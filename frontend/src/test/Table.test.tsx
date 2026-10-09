import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Table, type Column } from '../components/common/Table';

interface TestItem {
  id: string;
  name?: string;
  count?: number;
  optionalField?: string;
}

describe('Table Component', () => {
  const columns: Column<TestItem>[] = [
    { key: 'name', header: 'NAME' },
    { key: 'count', header: 'COUNT' },
    { key: 'optionalField', header: 'OPTIONAL' },
  ];

  it('renders table rows when actual data is provided', () => {
    const data: TestItem[] = [
      { id: '1', name: 'OpenAI', count: 42, optionalField: 'api.openai.com' },
      { id: '2', name: 'Anthropic', count: 18, optionalField: 'api.anthropic.com' },
    ];

    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
      />
    );

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('Anthropic')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('api.openai.com')).toBeInTheDocument();
  });

  it('renders neutral placeholder when optional field is missing', () => {
    const data: TestItem[] = [
      { id: '1', name: 'Cohere' }, // optionalField is missing
    ];

    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
      />
    );

    expect(screen.getByText('Cohere')).toBeInTheDocument();
    // Default fallback in Table for undefined fields is '-'
    expect(screen.getAllByText('-')).toHaveLength(2);
  });

  it('renders honest EmptyState when data array is empty', () => {
    render(
      <Table
        columns={columns}
        data={[]}
        keyExtractor={(item) => item.id}
        emptyTitle="No records found"
        emptyDescription="Awaiting backend ingestion."
      />
    );

    expect(screen.getByText('No records found')).toBeInTheDocument();
    expect(screen.getByText('Awaiting backend ingestion.')).toBeInTheDocument();
  });
});
