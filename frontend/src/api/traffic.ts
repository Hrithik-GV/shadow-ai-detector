import { apiClient } from './client';
import type { TrafficAnalysisResult, TrafficAnalyzeSubmitResponse } from '../types';

/**
 * Proposed Route: POST /api/traffic/analyze
 * Submits a network traffic capture file (CSV or JSON) for AI telemetry analysis.
 * Uses multipart/form-data as agreed in the API contract.
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

  return response.data;
}

/**
 * Proposed Route: GET /api/traffic/{analysis_id}
 * Retrieves results of a previous traffic analysis job.
 */
export async function getTrafficAnalysis(analysisId: string): Promise<TrafficAnalysisResult> {
  const response = await apiClient.get<TrafficAnalysisResult>(`/api/traffic/${analysisId}`);
  return response.data;
}
