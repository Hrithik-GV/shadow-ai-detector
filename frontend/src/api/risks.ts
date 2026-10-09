import { apiClient } from './client';
import type { RiskAssessment } from '../types';

/**
 * Proposed Route: GET /api/risks
 * Retrieves list of detected risk findings, policy violations, and data egress events.
 */
export async function getRiskAssessments(): Promise<RiskAssessment[]> {
  const response = await apiClient.get<RiskAssessment[]>('/api/risks');
  return response.data;
}
