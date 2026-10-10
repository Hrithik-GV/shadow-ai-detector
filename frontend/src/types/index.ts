export type RiskLevel = 'low' | 'medium' | 'high' | 'critical' | 'unknown';

/**
 * Standardized API Error schema across all endpoints
 */
export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}

/**
 * Health check response (GET /health)
 */
export interface ApiStatusResponse {
  status: string;
  version?: string;
  uptime?: number;
}

export interface DashboardActivityPoint {
  timestamp: string;
  count?: number;
  trafficCount?: number;
  aiFlowsCount?: number;
}

export interface ProviderDistributionItem {
  provider: string;
  count: number;
  percentage?: number;
}

export interface RecentlyObservedEndpoint {
  id?: string;
  endpoint: string;
  provider?: string;
  observedAt?: string;
  riskLevel?: RiskLevel;
  isApproved?: boolean;
}

/**
 * Dashboard summary statistics (GET /api/dashboard/stats)
 */
export interface DashboardStats {
  // Backend actual fields from GET /api/dashboard/stats
  scope?: string;
  analysis_id?: string;
  analyses_count?: number;
  scope_description?: string;
  total_records_received?: number;
  valid_records?: number;
  rejected_records?: number;
  unique_source_ips?: number;
  unique_destination_ips?: number;
  unique_destination_domains?: number;
  total_bytes_sent?: number;
  total_bytes_received?: number;
  bytes_sent_reported_count?: number;
  bytes_received_reported_count?: number;
  missing_bytes_sent_count?: number;
  missing_bytes_received_count?: number;
  protocols?: string[];
  protocol_distribution?: Record<string, number>;
  missing_protocol_count?: number;
  earliest_timestamp?: string;
  latest_timestamp?: string;
  records_with_timestamp?: number;
  missing_timestamp_count?: number;
  record_type_note?: string;
  byte_calculation_note?: string;

  // Frontend aliases and optional extensions
  totalTrafficEvents?: number;
  totalAnalyzedRecords?: number;
  totalTrafficRecords?: number;
  aiRelatedRecords?: number;
  aiTrafficEvents?: number;
  aiFlowsCount?: number;
  totalAiEndpoints?: number;
  totalEndpoints?: number;
  activeProvidersCount?: number;
  totalProviders?: number;
  unapprovedEndpointsCount?: number;
  flaggedRiskCount?: number;
  highRiskCount?: number;
  mediumRiskCount?: number;
  lowRiskCount?: number;
  criticalRiskCount?: number;
  riskBreakdown?: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
  };
  activityOverTime?: DashboardActivityPoint[];
  providerDistribution?: ProviderDistributionItem[] | Record<string, number>;
  recentlyObservedEndpoints?: RecentlyObservedEndpoint[];
  lastAnalysisTimestamp?: string;
  updatedAt?: string;
}

/**
 * Individual traffic record resulting from analysis
 */
export interface TrafficRecord {
  id?: string;
  analysis_id?: string;
  analysisId?: string;
  timestamp?: string;
  sourceIp?: string;
  source_ip?: string;
  destinationIp?: string;
  destination_ip?: string;
  destinationHost?: string;
  destinationDomain?: string;
  destination_domain?: string;
  destinationPort?: number;
  destination_port?: number;
  port?: number;
  protocol?: string;
  bytesSent?: number;
  bytes_sent?: number;
  bytesReceived?: number;
  bytes_received?: number;
  bytesTransferred?: number;
  http_method?: string;
  http_uri?: string;
  http_status_code?: number;
  user_agent?: string;
  sni_hostname?: string;
  classification?: string;
  riskLevel?: RiskLevel;
  risk_level?: RiskLevel;
  detectionEvidence?: string | string[];
  evidence?: string | string[];
  provider?: string;
  modelDetected?: string;
  flags?: string[];
}

/**
 * Traffic analysis summary
 */
export interface TrafficAnalysisSummary {
  totalPackets?: number;
  totalRecords?: number;
  total_valid_records?: number;
  total_bytes_sent?: number;
  total_bytes_received?: number;
  unique_source_ips?: number;
  unique_destination_domains?: number;
  unique_destination_ips?: number;
  aiFlowsDetected?: number;
  uniqueProviders?: number;
  highRiskFlows?: number;
  detectedProtocols?: string[];
  protocols?: string[];
  analyzedAt?: string;
  earliest_timestamp?: string;
  latest_timestamp?: string;
}

/**
 * Full traffic analysis result (GET /api/traffic/{analysis_id})
 */
export interface TrafficAnalysisResult {
  analysisId: string;
  id?: string;
  original_filename?: string;
  file_format?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | string;
  total_rows_received?: number;
  valid_rows?: number;
  rejected_rows?: number;
  createdAt?: string;
  created_at?: string;
  completedAt?: string;
  updated_at?: string;
  timestamp?: string;
  summary?: TrafficAnalysisSummary;
  records?: TrafficRecord[];
  totalRecords?: number;
  errorMessage?: string;
  error_details?: string | null;
}

/**
 * Traffic analysis submission response (POST /api/traffic/analyze)
 */
export interface TrafficAnalyzeSubmitResponse {
  id?: string;
  analysisId?: string;
  original_filename?: string;
  file_format?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | string;
  total_rows_received?: number;
  valid_rows?: number;
  rejected_rows?: number;
  error_details?: string | null;
  created_at?: string;
  updated_at?: string;
  summary?: TrafficAnalysisSummary;
  rejected_records?: unknown[];
  message?: string;
}

/**
 * AI Endpoint Inventory Item (GET /api/inventory)
 */
export interface EndpointInventoryItem {
  id: string;
  provider?: string;
  domain?: string;
  hostname?: string;
  url?: string;
  endpointAddress?: string;
  endpointType?: string;
  type?: string;
  category?: string;
  isApproved?: boolean;
  approvalStatus?: string;
  status?: string;
  confidence?: number;
  detectionConfidence?: number;
  totalCalls?: number;
  requestCount?: number;
  connectionCount?: number;
  observedRequests?: number;
  dataTransferred?: number | string;
  bytesTransferred?: number;
  riskLevel?: RiskLevel;
  riskScore?: number | string;
  reasons?: string[];
  riskReasons?: string[];
  evidence?: string | string[];
  detectionEvidence?: string | string[];
  detectionSignatures?: string[];
  firstSeenAt?: string;
  lastSeenAt?: string;
  investigationStatus?: string;
}

/**
 * Detailed Endpoint Record (GET /api/inventory/{endpoint_id})
 */
export interface EndpointDetail extends EndpointInventoryItem {
  allowedSubnets?: string[];
  observedModels?: string[];
  dataClassification?: string;
  detectionSignatures?: string[];
  evidence?: string | string[];
  explanation?: string;
  riskExplanation?: string;
  notes?: string;
}

/**
 * Risk Assessment Finding
 */
export interface RiskAssessment {
  id: string;
  target?: string;
  provider?: string;
  endpoint?: string;
  endpointHostname?: string;
  riskScore?: number | string;
  riskLevel?: RiskLevel;
  isApproved?: boolean;
  approvalStatus?: string;
  policyRule?: string;
  description?: string;
  reasons?: string[];
  evidence?: string | string[];
  firstSeenAt?: string;
  assessedAt?: string;
  investigationStatus?: string;
  status?: string;
}

/**
 * Test & evaluation metrics report (GET /api/reports/metrics)
 */
export interface TestEvaluationMetrics {
  totalEvaluations?: number;
  datasetSize?: number;
  evaluatedRecordsCount?: number;
  precision?: number | null;
  detectionPrecision?: number | null;
  recall?: number | null;
  detectionRecall?: number | null;
  falsePositiveRate?: number | null;
  fpr?: number | null;
  providerAccuracy?: number | null;
  providerIdentificationAccuracy?: number | null;
  detectionAccuracy?: number | null;
  truePositives?: number;
  falsePositives?: number;
  trueNegatives?: number;
  falseNegatives?: number;
  datasetVersion?: string;
  evaluationDatasetName?: string;
  isIllustrative?: boolean;
  notes?: string;
  status?: string;
  averageLatencyMs?: number;
  analyzedDataVolumeMb?: number;
  timestamp?: string;
  evaluatedAt?: string;
  lastGeneratedAt?: string;
  categoriesBreakdown?: Record<string, number>;
}

/**
 * AI Governance Policy Types (GET /api/policies)
 */
export type PolicyApprovalStatus = 'approved' | 'unapproved' | 'blocked' | 'restricted';

export interface AIGovernancePolicy {
  id: string;
  externalId?: string;
  external_id?: string;
  providerName?: string;
  provider_name?: string;
  domainSignatures?: string[];
  domain_signatures?: string[];
  approvalStatus?: PolicyApprovalStatus;
  approval_status?: PolicyApprovalStatus;
  isApproved?: boolean;
  is_approved?: boolean;
  isEnabled?: boolean;
  is_enabled?: boolean;
  policyRule?: string;
  policy_rule?: string;
  description?: string | null;
  createdBy?: string | null;
  created_by?: string | null;
  updatedBy?: string | null;
  updated_by?: string | null;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface PolicyAuditLog {
  id: string;
  policyId?: string | null;
  policy_id?: string | null;
  action: string;
  providerName?: string;
  provider_name?: string;
  previousState?: Record<string, unknown> | null;
  previous_state?: Record<string, unknown> | null;
  newState?: Record<string, unknown> | null;
  new_state?: Record<string, unknown> | null;
  performedBy?: string;
  performed_by?: string;
  details?: string | null;
  outcome?: string | null;
  timestamp: string;
}

export interface PolicySummaryMetrics {
  totalPolicies?: number;
  total_policies?: number;
  approvedPolicies?: number;
  approved_policies?: number;
  unapprovedPolicies?: number;
  unapproved_policies?: number;
  disabledPolicies?: number;
  disabled_policies?: number;
  activeApprovedProviders?: string[];
  active_approved_providers?: string[];
}

export interface PolicyCreatePayload {
  provider_name: string;
  domain_signatures: string[];
  approval_status: PolicyApprovalStatus;
  is_enabled?: boolean;
  policy_rule?: string;
  description?: string;
}

export interface PolicyUpdatePayload {
  provider_name?: string;
  domain_signatures?: string[];
  approval_status?: PolicyApprovalStatus;
  is_enabled?: boolean;
  policy_rule?: string;
  description?: string;
}

