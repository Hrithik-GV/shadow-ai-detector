import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type { ApiStatusResponse } from '../types';

export function useApiHealth() {
  return useQuery<ApiStatusResponse>({
    queryKey: ['apiHealth'],
    queryFn: async () => {
      const response = await apiClient.get<ApiStatusResponse>('/health');
      return response.data;
    },
    retry: 1,
    staleTime: 30000,
  });
}
