import { apiClient } from './client';
import type { TestEvaluationMetrics } from '../types';

/**
 * Proposed Route: GET /api/reports/metrics
 * Retrieves test evaluation metrics and model detection accuracy scores.
 */
export async function getReportMetrics(): Promise<TestEvaluationMetrics> {
  const response = await apiClient.get<TestEvaluationMetrics>('/api/reports/metrics');
  return response.data;
}
