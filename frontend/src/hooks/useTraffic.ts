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
  });
}

export function useSubmitTrafficFile() {
  const queryClient = useQueryClient();

  return useMutation<TrafficAnalyzeSubmitResponse, ApiError, File>({
    mutationFn: (file: File) => submitTrafficAnalysis(file),
    onSuccess: () => {
      // Invalidate relevant queries when a new analysis job is registered
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] });
      queryClient.invalidateQueries({ queryKey: ['traffic'] });
    },
  });
}
