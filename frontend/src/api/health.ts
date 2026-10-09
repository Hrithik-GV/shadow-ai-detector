import { apiClient } from './client';
import type { ApiStatusResponse } from '../types';

/**
 * Proposed Route: GET /health
 * Checks backend availability if implemented by the backend team.
 */
export async function checkBackendHealth(): Promise<ApiStatusResponse> {
  const response = await apiClient.get<ApiStatusResponse>('/health');
  return response.data;
}
