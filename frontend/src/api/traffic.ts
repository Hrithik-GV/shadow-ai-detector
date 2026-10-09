import { apiClient } from './client';
import type { TrafficAnalysisResult, TrafficAnalyzeSubmitResponse, TrafficRecord } from '../types';

/**
 * Route: POST /api/traffic/analyze
 * Submits a network traffic capture file (CSV or JSON) for AI telemetry analysis.
 * Uses multipart/form-data matching FastAPI endpoint contract.
 */
export async function submitTrafficAnalysis(
  file: File,
  onUploadProgress?: (progress: number) => void
): Promise<TrafficAnalyzeSubmitResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<TrafficAnalyzeSubmitResponse>(
    '/api/traffic/analyze',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // Extended timeout for file upload & processing
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onUploadProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percent);
        }
      },
    }
  );

  const data = response.data;
  const analysisId = data.id || data.analysisId || '';

  return {
    ...data,
    id: analysisId,
    analysisId,
  };
}

/**
 * Route: GET /api/traffic/{analysis_id}
 * Retrieves results and aggregated metrics for a traffic analysis job.
 * If records are partitioned into /records, fetches and combines them seamlessly.
 */
export async function getTrafficAnalysis(analysisId: string): Promise<TrafficAnalysisResult> {
  const response = await apiClient.get<Record<string, unknown>>(`/api/traffic/${analysisId}`);
  const detail = response.data;

  let records: TrafficRecord[] = Array.isArray(detail.records) ? (detail.records as TrafficRecord[]) : [];
  let totalRecords =
    (detail.totalRecords as number | undefined) ??
    (detail.total_rows_received as number | undefined) ??
    (records.length);

  // If records are not embedded directly in detail, fetch from /api/traffic/{analysis_id}/records
  if (!records || records.length === 0) {
    try {
      const recordsRes = await apiClient.get<{
        records?: unknown[];
        total_records?: number;
      }>(`/api/traffic/${analysisId}/records?limit=200`);

      if (recordsRes.data && Array.isArray(recordsRes.data.records)) {
        records = recordsRes.data.records.map((raw: unknown) => {
          const r = raw as Record<string, unknown>;
          return {
            id: r.id as string | undefined,
            timestamp: r.timestamp as string | undefined,
            sourceIp: (r.source_ip as string | undefined) ?? (r.sourceIp as string | undefined),
            source_ip: r.source_ip as string | undefined,
            destinationIp: (r.destination_ip as string | undefined) ?? (r.destinationIp as string | undefined),
            destination_ip: r.destination_ip as string | undefined,
            destinationDomain: (r.destination_domain as string | undefined) ?? (r.destinationDomain as string | undefined),
            destination_domain: r.destination_domain as string | undefined,
            destinationPort: (r.destination_port as number | undefined) ?? (r.destinationPort as number | undefined),
            destination_port: r.destination_port as number | undefined,
            protocol: r.protocol as string | undefined,
            bytesSent: (r.bytes_sent as number | undefined) ?? (r.bytesSent as number | undefined),
            bytes_sent: r.bytes_sent as number | undefined,
            bytesReceived: (r.bytes_received as number | undefined) ?? (r.bytesReceived as number | undefined),
            bytes_received: r.bytes_received as number | undefined,
            http_method: r.http_method as string | undefined,
            http_uri: r.http_uri as string | undefined,
            http_status_code: r.http_status_code as number | undefined,
            user_agent: r.user_agent as string | undefined,
            sni_hostname: r.sni_hostname as string | undefined,
            classification: (r.classification as string | undefined) ?? (r.sni_hostname ? 'AI Telemetry' : undefined),
            provider: (r.provider as string | undefined) ?? (r.sni_hostname as string | undefined) ?? (r.destination_domain as string | undefined),
            riskLevel: (r.riskLevel as any) ?? (r.risk_level as any),
            evidence: (r.evidence as string | undefined) ?? (r.sni_hostname as string | undefined) ?? (r.http_uri as string | undefined),
          };
        });
        totalRecords = recordsRes.data.total_records ?? totalRecords;
      }
    } catch {
      // Backend may not have records yet or analysis has zero records
    }
  }

  const summaryObj = (detail.summary as Record<string, unknown> | undefined) || {};

  return {
    analysisId: (detail.id as string | undefined) || (detail.analysisId as string | undefined) || analysisId,
    id: (detail.id as string | undefined) || analysisId,
    original_filename: detail.original_filename as string | undefined,
    file_format: detail.file_format as string | undefined,
    status: (detail.status as string | undefined) || 'completed',
    total_rows_received: detail.total_rows_received as number | undefined,
    valid_rows: detail.valid_rows as number | undefined,
    rejected_rows: detail.rejected_rows as number | undefined,
    createdAt: (detail.created_at as string | undefined) ?? (detail.createdAt as string | undefined),
    created_at: detail.created_at as string | undefined,
    completedAt: (detail.updated_at as string | undefined) ?? (detail.completedAt as string | undefined),
    updated_at: detail.updated_at as string | undefined,
    timestamp: (detail.created_at as string | undefined) ?? (detail.timestamp as string | undefined),
    totalRecords: totalRecords ?? records.length,
    summary: {
      totalPackets:
        (summaryObj.total_valid_records as number | undefined) ??
        (summaryObj.totalPackets as number | undefined) ??
        (detail.valid_rows as number | undefined),
      totalRecords:
        (summaryObj.total_valid_records as number | undefined) ??
        (summaryObj.totalRecords as number | undefined) ??
        (detail.total_rows_received as number | undefined),
      total_valid_records: summaryObj.total_valid_records as number | undefined,
      total_bytes_sent: summaryObj.total_bytes_sent as number | undefined,
      total_bytes_received: summaryObj.total_bytes_received as number | undefined,
      unique_source_ips: summaryObj.unique_source_ips as number | undefined,
      unique_destination_domains: summaryObj.unique_destination_domains as number | undefined,
      unique_destination_ips: summaryObj.unique_destination_ips as number | undefined,
      aiFlowsDetected:
        (summaryObj.aiFlowsDetected as number | undefined) ??
        (summaryObj.unique_destination_domains as number | undefined),
      uniqueProviders:
        (summaryObj.uniqueProviders as number | undefined) ??
        (summaryObj.unique_destination_domains as number | undefined),
      highRiskFlows: summaryObj.highRiskFlows as number | undefined,
      detectedProtocols:
        (summaryObj.protocols as string[] | undefined) ??
        (summaryObj.detectedProtocols as string[] | undefined),
      protocols: summaryObj.protocols as string[] | undefined,
      analyzedAt: (detail.created_at as string | undefined) ?? (summaryObj.analyzedAt as string | undefined),
    },
    records,
    errorMessage: (detail.error_details as string | undefined) || (detail.errorMessage as string | undefined),
    error_details: detail.error_details as string | null | undefined,
  };
}
