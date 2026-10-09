import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createPolicy,
  deletePolicy,
  disablePolicy,
  fetchPolicies,
  fetchPolicy,
  fetchPolicyAuditLogs,
  fetchPolicySummary,
  updatePolicy,
  updatePolicyStatus,
} from '../api/policies';
import type {
  AIGovernancePolicy,
  ApiError,
  PolicyAuditLog,
  PolicyCreatePayload,
  PolicySummaryMetrics,
  PolicyUpdatePayload,
} from '../types';

export const POLICIES_QUERY_KEY = ['policies'] as const;
export const POLICY_SUMMARY_QUERY_KEY = ['policy-summary'] as const;
export const POLICY_AUDIT_LOGS_QUERY_KEY = ['policy-audit-logs'] as const;

export function usePolicies(filters?: {
  is_enabled?: boolean;
  approval_status?: string;
  search?: string;
}) {
  return useQuery<AIGovernancePolicy[], ApiError>({
    queryKey: ['policies', filters],
    queryFn: () => fetchPolicies(filters),
    staleTime: 30000,
  });
}

export function usePolicySummary() {
  return useQuery<PolicySummaryMetrics, ApiError>({
    queryKey: POLICY_SUMMARY_QUERY_KEY,
    queryFn: fetchPolicySummary,
    staleTime: 30000,
  });
}

export function usePolicyDetail(policyId?: string) {
  return useQuery<AIGovernancePolicy, ApiError>({
    queryKey: ['policies', 'detail', policyId],
    queryFn: () => fetchPolicy(policyId!),
    enabled: Boolean(policyId),
  });
}

export function usePolicyAuditLogs(limit: number = 50) {
  return useQuery<PolicyAuditLog[], ApiError>({
    queryKey: ['policy-audit-logs', limit],
    queryFn: () => fetchPolicyAuditLogs(limit),
    staleTime: 30000,
  });
}

function invalidateRelevantQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ['policies'] });
  queryClient.invalidateQueries({ queryKey: POLICY_SUMMARY_QUERY_KEY });
  queryClient.invalidateQueries({ queryKey: POLICY_AUDIT_LOGS_QUERY_KEY });
  queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  queryClient.invalidateQueries({ queryKey: ['inventory'] });
  queryClient.invalidateQueries({ queryKey: ['risks'] });
  queryClient.invalidateQueries({ queryKey: ['reports'] });
}

export function useCreatePolicy() {
  const queryClient = useQueryClient();
  return useMutation<AIGovernancePolicy, ApiError, { payload: PolicyCreatePayload; token?: string }>({
    mutationFn: ({ payload, token }) => createPolicy(payload, token),
    onSuccess: () => {
      invalidateRelevantQueries(queryClient);
    },
  });
}

export function useUpdatePolicy() {
  const queryClient = useQueryClient();
  return useMutation<
    AIGovernancePolicy,
    ApiError,
    { policyId: string; payload: PolicyUpdatePayload; token?: string }
  >({
    mutationFn: ({ policyId, payload, token }) => updatePolicy(policyId, payload, token),
    onSuccess: () => {
      invalidateRelevantQueries(queryClient);
    },
  });
}

export function useUpdatePolicyStatus() {
  const queryClient = useQueryClient();
  return useMutation<
    AIGovernancePolicy,
    ApiError,
    { policyId: string; approvalStatus: string; notes?: string; token?: string }
  >({
    mutationFn: ({ policyId, approvalStatus, notes, token }) =>
      updatePolicyStatus(policyId, approvalStatus, notes, token),
    onSuccess: () => {
      invalidateRelevantQueries(queryClient);
    },
  });
}

export function useDisablePolicy() {
  const queryClient = useQueryClient();
  return useMutation<AIGovernancePolicy, ApiError, { policyId: string; token?: string }>({
    mutationFn: ({ policyId, token }) => disablePolicy(policyId, token),
    onSuccess: () => {
      invalidateRelevantQueries(queryClient);
    },
  });
}

export function useDeletePolicy() {
  const queryClient = useQueryClient();
  return useMutation<{ success: boolean; message: string }, ApiError, { policyId: string; token?: string }>({
    mutationFn: ({ policyId, token }) => deletePolicy(policyId, token),
    onSuccess: () => {
      invalidateRelevantQueries(queryClient);
    },
  });
}
