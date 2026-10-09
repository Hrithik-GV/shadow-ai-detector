import { apiClient } from './client';
import type {
  AIGovernancePolicy,
  PolicyAuditLog,
  PolicyCreatePayload,
  PolicySummaryMetrics,
  PolicyUpdatePayload,
} from '../types';

export const ADMIN_TOKEN_STORAGE_KEY = 'shadow_ai_admin_token';
export const DEFAULT_ADMIN_TOKEN = 'shadow-ai-admin-secret-key';

export function getEffectiveAdminToken(): string {
  try {
    const stored = localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
    if (stored !== null && stored.trim() !== '') {
      return stored.trim();
    }
  } catch {
    // ignore local storage security errors
  }
  return DEFAULT_ADMIN_TOKEN;
}

export function setStoredAdminToken(token: string): void {
  try {
    localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, token.trim());
  } catch {
    // ignore
  }
}

function getAuthHeaders(token?: string) {
  const activeToken = token || getEffectiveAdminToken();
  return activeToken ? { 'X-Admin-Token': activeToken } : {};
}

/**
 * Fetch all AI governance policies
 */
export async function fetchPolicies(filters?: {
  is_enabled?: boolean;
  approval_status?: string;
  search?: string;
}): Promise<AIGovernancePolicy[]> {
  const params: Record<string, unknown> = {};
  if (filters?.is_enabled !== undefined) params.is_enabled = filters.is_enabled;
  if (filters?.approval_status) params.approval_status = filters.approval_status;
  if (filters?.search) params.search = filters.search;

  const response = await apiClient.get<AIGovernancePolicy[]>('/api/policies', { params });
  return response.data;
}

/**
 * Fetch policy overview summary statistics
 */
export async function fetchPolicySummary(): Promise<PolicySummaryMetrics> {
  const response = await apiClient.get<PolicySummaryMetrics>('/api/policies/summary');
  return response.data;
}

/**
 * Fetch an individual policy by UUID or external ID
 */
export async function fetchPolicy(policyId: string): Promise<AIGovernancePolicy> {
  const response = await apiClient.get<AIGovernancePolicy>(`/api/policies/${encodeURIComponent(policyId)}`);
  return response.data;
}

/**
 * Create a new AI governance policy (Admin required)
 */
export async function createPolicy(
  payload: PolicyCreatePayload,
  token?: string
): Promise<AIGovernancePolicy> {
  const response = await apiClient.post<AIGovernancePolicy>('/api/policies', payload, {
    headers: getAuthHeaders(token),
  });
  return response.data;
}

/**
 * Update policy configuration settings (Admin required)
 */
export async function updatePolicy(
  policyId: string,
  payload: PolicyUpdatePayload,
  token?: string
): Promise<AIGovernancePolicy> {
  const response = await apiClient.put<AIGovernancePolicy>(
    `/api/policies/${encodeURIComponent(policyId)}`,
    payload,
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Quick toggle approval status (Admin required)
 */
export async function updatePolicyStatus(
  policyId: string,
  approvalStatus: string,
  notes?: string,
  token?: string
): Promise<AIGovernancePolicy> {
  const response = await apiClient.patch<AIGovernancePolicy>(
    `/api/policies/${encodeURIComponent(policyId)}/status`,
    { approval_status: approvalStatus, notes },
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Safely disable a policy rule (Admin required)
 */
export async function disablePolicy(policyId: string, token?: string): Promise<AIGovernancePolicy> {
  const response = await apiClient.post<AIGovernancePolicy>(
    `/api/policies/${encodeURIComponent(policyId)}/disable`,
    {},
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Delete a policy rule (Admin required)
 */
export async function deletePolicy(policyId: string, token?: string): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(
    `/api/policies/${encodeURIComponent(policyId)}`,
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Fetch chronological policy audit logs
 */
export async function fetchPolicyAuditLogs(limit: number = 50): Promise<PolicyAuditLog[]> {
  const response = await apiClient.get<PolicyAuditLog[]>('/api/policies/audit-logs', {
    params: { limit },
  });
  return response.data;
}
