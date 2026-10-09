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
  timestamp?: string;
  sourceIp?: string;
  destinationIp?: string;
  destinationHost?: string;
  destinationDomain?: string;
  destinationPort?: number;
  port?: number;
  protocol?: string;
  bytesSent?: number;
  bytesReceived?: number;
  bytesTransferred?: number;
  classification?: string;
  riskLevel?: RiskLevel;
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
  aiFlowsDetected?: number;
  uniqueProviders?: number;
  highRiskFlows?: number;
  detectedProtocols?: string[];
  analyzedAt?: string;
}

/**
 * Full traffic analysis result (GET /api/traffic/{analysis_id})
 */
export interface TrafficAnalysisResult {
  analysisId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt?: string;
  completedAt?: string;
  timestamp?: string;
  summary?: TrafficAnalysisSummary;
  records?: TrafficRecord[];
  totalRecords?: number;
  errorMessage?: string;
}

/**
 * Traffic analysis submission response (POST /api/traffic/analyze)
 */
export interface TrafficAnalyzeSubmitResponse {
  analysisId: string;
  status: 'pending' | 'processing' | 'completed';
  message: string;
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
  precision?: number;
  detectionPrecision?: number;
  recall?: number;
  detectionRecall?: number;
  falsePositiveRate?: number;
  fpr?: number;
  providerAccuracy?: number;
  providerIdentificationAccuracy?: number;
  detectionAccuracy?: number;
  averageLatencyMs?: number;
  analyzedDataVolumeMb?: number;
  timestamp?: string;
  evaluatedAt?: string;
  lastGeneratedAt?: string;
  categoriesBreakdown?: Record<string, number>;
}
