import { useQuery } from '@tanstack/react-query';
import { getReportMetrics } from '../api/reports';
import type { TestEvaluationMetrics, ApiError } from '../types';

export const REPORTS_METRICS_QUERY_KEY = ['reports', 'metrics'] as const;

export function useReportMetrics(options?: { retry?: boolean | number }) {
  return useQuery<TestEvaluationMetrics, ApiError>({
    queryKey: REPORTS_METRICS_QUERY_KEY,
    queryFn: getReportMetrics,
    retry: options?.retry ?? 1,
    staleTime: 60000,
  });
}
