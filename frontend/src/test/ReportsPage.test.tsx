import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReportsPage } from '../pages/ReportsPage';
import * as reportsApi from '../api/reports';

vi.mock('../api/reports');

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe('ReportsPage', () => {
  it('displays real evaluation metrics when returned by API response', async () => {
    vi.mocked(reportsApi.getReportMetrics).mockResolvedValueOnce({
      precision: 0.965,
      recall: 0.942,
      falsePositiveRate: 0.021,
      providerAccuracy: 0.985,
      datasetSize: 15400,
      evaluatedAt: '2026-10-09 18:00:00 UTC',
    });

    renderWithClient(<ReportsPage retry={false} />);

    expect(await screen.findByText('96.5%')).toBeInTheDocument();
    expect(screen.getByText('94.2%')).toBeInTheDocument();
    expect(screen.getByText('2.1%')).toBeInTheDocument();
    expect(screen.getByText('98.5%')).toBeInTheDocument();
    expect(screen.getByText('15,400 records')).toBeInTheDocument();
    expect(screen.getByText(/2026-10-09 18:00:00 UTC/)).toBeInTheDocument();
  });

  it('displays "No evaluation results available." when evaluation has not been run', async () => {
    vi.mocked(reportsApi.getReportMetrics).mockResolvedValueOnce({});

    renderWithClient(<ReportsPage retry={false} />);

    expect(await screen.findByText('No evaluation results available.')).toBeInTheDocument();
  });

  it('displays error state when API request fails', async () => {
    vi.mocked(reportsApi.getReportMetrics).mockRejectedValueOnce({
      message: 'Failed to fetch evaluation metrics',
      status: 500,
    });

    renderWithClient(<ReportsPage retry={false} />);

    expect(await screen.findByText('Reports API Error')).toBeInTheDocument();
    expect(screen.getByText('Failed to fetch evaluation metrics')).toBeInTheDocument();
  });
});
