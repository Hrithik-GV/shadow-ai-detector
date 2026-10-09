import { apiClient } from './client';
import type { EndpointInventoryItem, EndpointDetail } from '../types';

/**
 * Proposed Route: GET /api/inventory
 * Retrieves catalog of all discovered AI service endpoints and providers.
 */
export async function getInventory(): Promise<EndpointInventoryItem[]> {
  const response = await apiClient.get<EndpointInventoryItem[]>('/api/inventory');
  return response.data;
}

/**
 * Proposed Route: GET /api/inventory/{endpoint_id}
 * Retrieves detailed metadata for a specific AI endpoint.
 */
export async function getEndpointDetail(endpointId: string): Promise<EndpointDetail> {
  const response = await apiClient.get<EndpointDetail>(`/api/inventory/${endpointId}`);
  return response.data;
}
