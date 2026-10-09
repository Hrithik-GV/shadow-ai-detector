import { apiClient } from './client';
import type { DashboardStats } from '../types';

/**
 * Proposed Route: GET /api/dashboard/stats
 * Retrieves top-level operational counts, provider stats, and risk summary.
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>('/api/dashboard/stats');
  return response.data;
}
