import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LoadingState } from '../components/common/LoadingState';
import { QueryErrorState } from '../components/common/QueryErrorState';
import { EmptyState } from '../components/common/EmptyState';

describe('Common UI State Components', () => {
  it('renders LoadingState with custom or default message', () => {
    const { rerender } = render(<LoadingState />);
    expect(screen.getByText('CONNECTING TO INGESTION API...')).toBeInTheDocument();

    rerender(<LoadingState message="PARSING TELEMETRY..." />);
    expect(screen.getByText('PARSING TELEMETRY...')).toBeInTheDocument();
  });

  it('renders EmptyState with title, description, and status label', () => {
    render(
      <EmptyState
        title="No Telemetry Streams Active"
        description="Connect a network probe to ingest packets."
        statusLabel="IDLE"
      />
    );

    expect(screen.getByText('No Telemetry Streams Active')).toBeInTheDocument();
    expect(screen.getByText('Connect a network probe to ingest packets.')).toBeInTheDocument();
    expect(screen.getByText('IDLE')).toBeInTheDocument();
  });

  it('renders QueryErrorState with error message, status code, and calls retry callback on button click', () => {
    const onRetryMock = vi.fn();

    render(
      <QueryErrorState
        title="API Gateway Failed"
        error={{
          message: 'Connection refused on port 8000',
          status: 503,
          code: 'SERVICE_UNAVAILABLE',
        }}
        onRetry={onRetryMock}
      />
    );

    expect(screen.getByText('API Gateway Failed')).toBeInTheDocument();
    expect(screen.getByText('Connection refused on port 8000')).toBeInTheDocument();
    expect(screen.getByText('HTTP 503')).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /retry request/i });
    expect(retryBtn).toBeInTheDocument();

    fireEvent.click(retryBtn);
    expect(onRetryMock).toHaveBeenCalledTimes(1);
  });
});
