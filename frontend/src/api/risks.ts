import { apiClient } from './client';
import type { RiskAssessment, EndpointInventoryItem } from '../types';

/**
 * Retrieves risk findings adhering to the agreed API contract.
 * If a dedicated /api/risks endpoint is not provided (404), extracts risk fields
 * directly from GET /api/inventory rather than failing on an unagreed route.
 */
export async function getRiskAssessments(): Promise<RiskAssessment[]> {
  try {
    const response = await apiClient.get<RiskAssessment[]>('/api/risks');
    return response.data;
  } catch (err: unknown) {
    const errObj = err as { status?: number };
    // If /api/risks is not available (404), safely query agreed GET /api/inventory
    if (errObj && errObj.status === 404) {
      const inventoryRes = await apiClient.get<EndpointInventoryItem[]>('/api/inventory');
      const items = inventoryRes.data || [];
      return items.map((item) => ({
        id: `RISK-${item.id}`,
        target: item.hostname || item.url || item.domain || item.endpointAddress || item.id,
        provider: item.provider,
        endpoint: item.url || item.hostname || item.domain,
        endpointHostname: item.hostname || item.domain,
        riskScore: item.riskScore,
        riskLevel: item.riskLevel,
        isApproved: item.isApproved,
        approvalStatus: item.approvalStatus,
        policyRule: item.category ? `Classification Policy: ${item.category}` : undefined,
        description: Array.isArray(item.reasons) ? item.reasons.join('; ') : undefined,
        reasons: item.reasons || item.riskReasons,
        evidence: item.evidence || item.detectionEvidence || item.detectionSignatures,
        firstSeenAt: item.firstSeenAt,
        assessedAt: item.lastSeenAt || item.firstSeenAt,
        investigationStatus: item.investigationStatus,
        status: item.status,
      }));
    }
    throw err;
  }
}
