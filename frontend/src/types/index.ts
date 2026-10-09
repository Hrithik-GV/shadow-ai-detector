export type RiskLevel = 'low' | 'medium' | 'high' | 'critical' | 'unknown';

export interface AIProvider {
  id: string;
  name: string;
  domain: string;
  category: string;
  riskScore?: number;
  riskLevel?: RiskLevel;
  firstSeenAt?: string;
  lastSeenAt?: string;
}

export interface AIEndpoint {
  id: string;
  providerId: string;
  url: string;
  protocol: string;
  isApproved: boolean;
  riskLevel: RiskLevel;
}

export interface NetworkTrafficEvent {
  id: string;
  timestamp: string;
  sourceIp: string;
  destinationIp: string;
  destinationHost: string;
  port: number;
  protocol: string;
  providerId?: string;
  bytesSent: number;
  bytesReceived: number;
  riskLevel: RiskLevel;
}

export interface RiskClassification {
  id: string;
  target: string;
  riskLevel: RiskLevel;
  reasons: string[];
  assessedAt: string;
  status: 'active' | 'resolved' | 'investigating';
}

export interface ApiStatusResponse {
  status: string;
  version?: string;
  uptime?: number;
}
