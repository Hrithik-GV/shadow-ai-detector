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

  it('displays confusion matrix counts and versioned benchmark dataset info', async () => {
    vi.mocked(reportsApi.getReportMetrics).mockResolvedValueOnce({
      precision: 1.0,
      recall: 1.0,
      falsePositiveRate: 0.0,
      providerAccuracy: 1.0,
      datasetSize: 20,
      truePositives: 10,
      falsePositives: 0,
      trueNegatives: 10,
      falseNegatives: 0,
      datasetVersion: '1.0.0',
      evaluationDatasetName: 'shadow_ai_ground_truth_benchmark_v1',
      evaluatedAt: '2026-10-10 00:00:00 UTC',
    });

    renderWithClient(<ReportsPage retry={false} />);

    expect(await screen.findByText('Ground-Truth Confusion Matrix')).toBeInTheDocument();
    expect(screen.getByText('True Positives (TP)')).toBeInTheDocument();
    expect(screen.getByText('False Positives (FP)')).toBeInTheDocument();
    expect(screen.getByText('True Negatives (TN)')).toBeInTheDocument();
    expect(screen.getByText('False Negatives (FN)')).toBeInTheDocument();
    expect(screen.getByText('VERSION 1.0.0')).toBeInTheDocument();
    expect(screen.getByText(/shadow_ai_ground_truth_benchmark_v1/)).toBeInTheDocument();
  });

  it('handles null metrics for zero denominator cases gracefully without crashing', async () => {
    vi.mocked(reportsApi.getReportMetrics).mockResolvedValueOnce({
      precision: null,
      recall: null,
      falsePositiveRate: null,
      providerAccuracy: null,
      datasetSize: 0,
      truePositives: 0,
      falsePositives: 0,
      trueNegatives: 0,
      falseNegatives: 0,
      datasetVersion: '1.0.0',
      evaluatedAt: '2026-10-10 00:00:00 UTC',
    });

    renderWithClient(<ReportsPage retry={false} />);

    expect(await screen.findByText('Ground-Truth Benchmark Summary')).toBeInTheDocument();
    expect(screen.getAllByText('Not available').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/0 records/)).toBeInTheDocument();
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
