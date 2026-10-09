import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '../api/dashboard';
import type { DashboardStats, ApiError } from '../types';

export const DASHBOARD_STATS_QUERY_KEY = ['dashboard', 'stats'] as const;

export function useDashboardStats() {
  return useQuery<DashboardStats, ApiError>({
    queryKey: DASHBOARD_STATS_QUERY_KEY,
    queryFn: getDashboardStats,
    retry: 1,
    staleTime: 60000,
  });
}
