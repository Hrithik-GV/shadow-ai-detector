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

/**
 * Dashboard summary statistics (GET /api/dashboard/stats)
 */
export interface DashboardStats {
  totalTrafficEvents: number;
  totalAiEndpoints: number;
  unapprovedEndpointsCount: number;
  flaggedRiskCount: number;
  activeProvidersCount: number;
  lastAnalysisTimestamp?: string;
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
  totalEvaluations: number;
  detectionAccuracy?: number;
  falsePositiveRate?: number;
  averageLatencyMs?: number;
  analyzedDataVolumeMb?: number;
  lastGeneratedAt?: string;
  categoriesBreakdown?: Record<string, number>;
}
