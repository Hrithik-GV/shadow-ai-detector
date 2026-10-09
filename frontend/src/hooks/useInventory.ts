import { useQuery } from '@tanstack/react-query';
import { getInventory, getEndpointDetail } from '../api/inventory';
import type { EndpointInventoryItem, EndpointDetail, ApiError } from '../types';

export const INVENTORY_QUERY_KEY = ['inventory', 'list'] as const;
export const ENDPOINT_DETAIL_QUERY_KEY = (id: string) => ['inventory', 'detail', id] as const;

export function useInventory() {
  return useQuery<EndpointInventoryItem[], ApiError>({
    queryKey: INVENTORY_QUERY_KEY,
    queryFn: getInventory,
    retry: 1,
    staleTime: 60000,
  });
}

export function useEndpointDetail(endpointId?: string) {
  return useQuery<EndpointDetail, ApiError>({
    queryKey: ENDPOINT_DETAIL_QUERY_KEY(endpointId || ''),
    queryFn: () => getEndpointDetail(endpointId!),
    enabled: Boolean(endpointId),
    retry: 1,
  });
}
