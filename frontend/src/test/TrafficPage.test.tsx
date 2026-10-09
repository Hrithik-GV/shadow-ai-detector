import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TrafficPage } from '../pages/TrafficPage';
import * as trafficApi from '../api/traffic';

vi.mock('../api/traffic');

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

describe('TrafficPage PCAP & Capture Ingestion', () => {
  it('renders upload dropzone with PCAP and PCAPNG support badges and limits notice', () => {
    renderWithClient(<TrafficPage />);

    expect(screen.getByText('Traffic Capture & Log File Ingestion')).toBeInTheDocument();
    expect(screen.getByText('PCAP')).toBeInTheDocument();
    expect(screen.getByText('PCAPNG')).toBeInTheDocument();
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText('Capture Analysis Scope & Wire Byte Semantics')).toBeInTheDocument();
  });

  it('validates file extension and rejects unsupported formats', async () => {
    renderWithClient(<TrafficPage />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();

    const badFile = new File(['dummy binary'], 'malicious.exe', { type: 'application/octet-stream' });
    fireEvent.change(input, { target: { files: [badFile] } });

    expect(await screen.findByText(/Unsupported file format/i)).toBeInTheDocument();
  });

  it('accepts valid .pcap capture file and displays file information', async () => {
    renderWithClient(<TrafficPage />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const pcapFile = new File([new ArrayBuffer(1024)], 'traffic_sample.pcap', {
      type: 'application/vnd.tcpdump.pcap',
    });

    fireEvent.change(input, { target: { files: [pcapFile] } });

    expect(await screen.findByText('traffic_sample.pcap')).toBeInTheDocument();
    expect(screen.queryByText(/Unsupported file format/i)).not.toBeInTheDocument();
    expect(screen.getByText('SUBMIT FOR ANALYSIS')).toBeInTheDocument();
  });

  it('displays completed analysis results with PCAP badge, valid flow counts, and wire byte footnote', async () => {
    vi.mocked(trafficApi.getTrafficAnalysis).mockResolvedValueOnce({
      analysisId: 'ANALYSIS-PCAP-TEST-001',
      id: 'ANALYSIS-PCAP-TEST-001',
      original_filename: 'network_capture.pcapng',
      file_format: 'pcapng',
      status: 'completed',
      total_rows_received: 150,
      valid_rows: 148,
      rejected_rows: 2,
      totalRecords: 1,
      summary: {
        totalPackets: 150,
        aiFlowsDetected: 1,
        uniqueProviders: 1,
        highRiskFlows: 1,
      },
      records: [
        {
          id: 'REC-001',
          source_ip: '192.168.1.50',
          destination_ip: '104.18.7.192',
          destination_domain: 'api.openai.com',
          destination_port: 443,
          protocol: 'TLS',
          bytes_sent: 1240,
          bytes_received: 4500,
          risk_level: 'critical',
          provider: 'OpenAI',
          classification: 'critical',
          evidence: 'TLS Server Name Indication (SNI) Handshake',
        },
      ],
    });

    vi.mocked(trafficApi.submitTrafficAnalysis).mockResolvedValueOnce({
      id: 'ANALYSIS-PCAP-TEST-001',
      analysisId: 'ANALYSIS-PCAP-TEST-001',
      original_filename: 'network_capture.pcapng',
      file_format: 'pcapng',
      status: 'completed',
      total_rows_received: 150,
      valid_rows: 148,
      rejected_rows: 2,
    });

    renderWithClient(<TrafficPage />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const pcapFile = new File([new ArrayBuffer(1024)], 'network_capture.pcapng', {
      type: 'application/octet-stream',
    });

    fireEvent.change(input, { target: { files: [pcapFile] } });
    const submitBtn = screen.getByText('SUBMIT FOR ANALYSIS');
    fireEvent.click(submitBtn);

    expect(await screen.findByText('api.openai.com', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getByText('148 valid flows parsed')).toBeInTheDocument();
    expect(screen.getByText(/2 packets or frames were rejected/i)).toBeInTheDocument();
    expect(screen.getAllByText('PCAPNG').length).toBeGreaterThan(0);
    expect(screen.getByText(/Wire Byte Counts: Measured as total Layer 3 IP datagram length/i)).toBeInTheDocument();
  });
});
