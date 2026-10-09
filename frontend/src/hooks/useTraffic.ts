import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTrafficAnalysis, submitTrafficAnalysis } from '../api/traffic';
import type { TrafficAnalysisResult, TrafficAnalyzeSubmitResponse, ApiError } from '../types';

export const TRAFFIC_ANALYSIS_QUERY_KEY = (id: string) => ['traffic', 'analysis', id] as const;

export function useTrafficAnalysis(analysisId?: string) {
  return useQuery<TrafficAnalysisResult, ApiError>({
    queryKey: TRAFFIC_ANALYSIS_QUERY_KEY(analysisId || ''),
    queryFn: () => getTrafficAnalysis(analysisId!),
    enabled: Boolean(analysisId),
    retry: 1,
    // Automatically poll status every 3s if status is pending or processing
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'pending' || data.status === 'processing')) {
        return 3000;
      }
      return false;
    },
  });
}

export interface SubmitTrafficFileParams {
  file: File;
  onProgress?: (progress: number) => void;
}

export function useSubmitTrafficFile() {
  const queryClient = useQueryClient();

  return useMutation<TrafficAnalyzeSubmitResponse, ApiError, SubmitTrafficFileParams>({
    mutationFn: ({ file, onProgress }) => submitTrafficAnalysis(file, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['traffic'] });
    },
  });
}
