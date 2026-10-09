import { useQuery } from '@tanstack/react-query';
import { getRiskAssessments } from '../api/risks';
import type { RiskAssessment, ApiError } from '../types';

export const RISKS_QUERY_KEY = ['risks', 'list'] as const;

export function useRisks() {
  return useQuery<RiskAssessment[], ApiError>({
    queryKey: RISKS_QUERY_KEY,
    queryFn: getRiskAssessments,
    retry: 1,
    staleTime: 60000,
  });
}
