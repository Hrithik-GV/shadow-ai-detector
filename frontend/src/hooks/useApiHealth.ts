import { useQuery } from '@tanstack/react-query';
import { checkBackendHealth } from '../api/health';
import type { ApiStatusResponse, ApiError } from '../types';

export const HEALTH_QUERY_KEY = ['backendHealth'] as const;

export function useApiHealth() {
  return useQuery<ApiStatusResponse, ApiError>({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: checkBackendHealth,
    retry: 1,
    staleTime: 15000,
    refetchInterval: 30000,
  });
}
