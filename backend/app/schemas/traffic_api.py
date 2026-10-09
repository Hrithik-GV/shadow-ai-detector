from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.traffic import RecordValidationError


class TrafficMetricsSummary(BaseModel):
    """Aggregate metrics derived strictly from actual processed/persisted traffic records."""
    model_config = ConfigDict(from_attributes=True)

    # Record Counts vs Network Connections
    total_records_received: int = Field(0, description="Total raw log records received in the capture file")
    valid_records: int = Field(0, description="Number of log records that passed schema validation and were persisted")
    total_valid_records: int = Field(0, description="Count of valid traffic records in this analysis (alias of valid_records)")
    rejected_records: int = Field(0, description="Number of raw log records rejected during validation")

    # Network Identifiers (excluding null/missing values)
    unique_source_ips: int = Field(0, description="Count of distinct source IP addresses observed (excluding nulls)")
    unique_destination_ips: int = Field(0, description="Count of distinct destination IP addresses observed (excluding nulls)")
    unique_destination_domains: int = Field(0, description="Count of distinct destination domains observed (excluding nulls)")

    # Bytes (calculated only from valid available values)
    total_bytes_sent: int = Field(0, description="Sum of bytes sent across records where bytes_sent is known")
    total_bytes_received: int = Field(0, description="Sum of bytes received across records where bytes_received is known")
    bytes_sent_reported_count: int = Field(0, description="Count of records with non-null bytes_sent value")
    bytes_received_reported_count: int = Field(0, description="Count of records with non-null bytes_received value")
    missing_bytes_sent_count: int = Field(0, description="Count of valid records where bytes_sent was omitted/null")
    missing_bytes_received_count: int = Field(0, description="Count of valid records where bytes_received was omitted/null")

    # Protocol Distribution
    protocols: List[str] = Field(default_factory=list, description="Sorted list of distinct network protocols observed")
    protocol_distribution: Dict[str, int] = Field(default_factory=dict, description="Frequency map of observed protocols (e.g. {'TCP': 10, 'UDP': 2})")
    missing_protocol_count: int = Field(0, description="Count of records with omitted/unknown protocol")

    # Timestamps
    earliest_timestamp: Optional[datetime] = Field(None, description="Earliest observed event timestamp")
    latest_timestamp: Optional[datetime] = Field(None, description="Latest observed event timestamp")
    records_with_timestamp: int = Field(0, description="Count of records with non-null timestamp")
    missing_timestamp_count: int = Field(0, description="Count of records with omitted timestamp")

    # Clarification notes
    record_type_note: str = Field(
        "Counts represent ingested log records/events, which may or may not map 1:1 to unique TCP/network connections.",
        description="Clarification distinguishing log record count from network connections",
    )
    byte_calculation_note: str = Field(
        "Missing byte counts are treated as unknown (null) and excluded from summation, not counted as zero.",
        description="Clarification on how missing byte metrics affect totals",
    )


class TrafficRecordResponse(BaseModel):
    """Schema for individual persisted traffic record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_id: uuid.UUID
    timestamp: Optional[datetime] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    destination_domain: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    http_method: Optional[str] = None
    http_uri: Optional[str] = None
    http_status_code: Optional[int] = None
    user_agent: Optional[str] = None
    sni_hostname: Optional[str] = None


class TrafficAnalysisListItem(BaseModel):
    """Brief metadata summary of a traffic analysis job for history listings."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_format: str
    status: str
    total_rows_received: int
    valid_rows: int
    rejected_rows: int
    error_details: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TrafficAnalysisDetailResponse(BaseModel):
    """Detailed view of an analysis job including its real computed metrics summary."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_format: str
    status: str
    total_rows_received: int
    valid_rows: int
    rejected_rows: int
    error_details: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    summary: TrafficMetricsSummary


class TrafficAnalyzeResponse(BaseModel):
    """Response returned immediately after file upload and ingestion."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_format: str
    status: str
    total_rows_received: int
    valid_rows: int
    rejected_rows: int
    error_details: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    summary: TrafficMetricsSummary
    rejected_records: List[RecordValidationError] = Field(
        default_factory=list,
        description="Detailed diagnostics for rows that failed validation",
    )


class PaginatedTrafficRecordsResponse(BaseModel):
    """Paginated list of persisted records for a given analysis run."""
    analysis_id: uuid.UUID
    total_records: int
    limit: int
    offset: int
    records: List[TrafficRecordResponse]


class PaginatedTrafficAnalysesResponse(BaseModel):
    """Paginated list of traffic analysis history."""
    total_analyses: int
    limit: int
    offset: int
    analyses: List[TrafficAnalysisListItem]


class DashboardStatsResponse(BaseModel):
    """Aggregated real summary statistics for the frontend Overview page."""
    model_config = ConfigDict(from_attributes=True)

    scope: str = Field(..., description="Scope of statistics: 'all_analyses' or 'selected_analysis'")
    analysis_id: Optional[uuid.UUID] = Field(None, description="Analysis ID if scoped to a specific analysis, otherwise null")
    analyses_count: int = Field(..., description="Number of analysis jobs included in these statistics")
    scope_description: str = Field(..., description="Explanation of whether statistics cover all analyses or a selected analysis")

    # Aggregate record counts
    total_records_received: int = Field(0, description="Total raw log records received across the included analyses")
    valid_records: int = Field(0, description="Total valid persisted records")
    rejected_records: int = Field(0, description="Total rejected records")

    # Network identifiers (excluding nulls)
    unique_source_ips: int = Field(0, description="Count of distinct source IP addresses observed (excluding nulls)")
    unique_destination_ips: int = Field(0, description="Count of distinct destination IP addresses observed (excluding nulls)")
    unique_destination_domains: int = Field(0, description="Count of distinct destination domains observed (excluding nulls)")

    # Bytes (calculated only from valid available values)
    total_bytes_sent: int = Field(0, description="Sum of bytes sent across records where bytes_sent is known")
    total_bytes_received: int = Field(0, description="Sum of bytes received across records where bytes_received is known")
    bytes_sent_reported_count: int = Field(0, description="Count of records with non-null bytes_sent value")
    bytes_received_reported_count: int = Field(0, description="Count of records with non-null bytes_received value")
    missing_bytes_sent_count: int = Field(0, description="Count of valid records where bytes_sent was omitted")
    missing_bytes_received_count: int = Field(0, description="Count of valid records where bytes_received was omitted")

    # Protocols
    protocols: List[str] = Field(default_factory=list, description="List of distinct network protocols observed")
    protocol_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of observed protocols")
    missing_protocol_count: int = Field(0, description="Count of records with omitted/unknown protocol")

    # Timestamps
    earliest_timestamp: Optional[datetime] = Field(None, description="Earliest observed timestamp")
    latest_timestamp: Optional[datetime] = Field(None, description="Latest observed timestamp")
    records_with_timestamp: int = Field(0, description="Count of records with valid timestamp")
    missing_timestamp_count: int = Field(0, description="Count of records with omitted timestamp")

    # Clarification notes
    record_type_note: str = Field(
        "Counts represent ingested log records/events, which may or may not map 1:1 to unique TCP/network connections.",
        description="Clarification distinguishing log record count from network connections",
    )
    byte_calculation_note: str = Field(
        "Missing byte counts are treated as unknown (null) and excluded from summation, not counted as zero.",
        description="Clarification on how missing byte metrics affect totals",
    )

    # Real AI Governance & Risk Telemetry
    aiRelatedRecords: int = Field(0, description="Count of network log records targeting confirmed AI services")
    totalAiEndpoints: int = Field(0, description="Count of distinct AI destination endpoints cataloged")
    activeProvidersCount: int = Field(0, description="Count of distinct active AI providers observed")
    unapprovedEndpointsCount: int = Field(0, description="Count of unapproved shadow AI endpoints detected")
    flaggedRiskCount: int = Field(0, description="Total active security/policy risk findings")
    highRiskCount: int = Field(0, description="Count of high severity risk findings")
    mediumRiskCount: int = Field(0, description="Count of medium severity risk findings")
    lowRiskCount: int = Field(0, description="Count of low severity risk findings")
    criticalRiskCount: int = Field(0, description="Count of critical severity risk findings")
    riskBreakdown: Dict[str, int] = Field(default_factory=dict, description="Breakdown of findings by severity")
    providerDistribution: Dict[str, int] = Field(default_factory=dict, description="Frequency breakdown by AI provider")
    recentlyObservedEndpoints: List[Dict[str, Any]] = Field(default_factory=list, description="Recent AI endpoints observed")


class EndpointInventoryItemResponse(BaseModel):
    """Schema for AI endpoint inventory item matching the frontend API contract."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    provider: str
    domain: str
    hostname: str
    url: str
    endpointAddress: str
    endpoint_address: str
    endpointType: str
    endpoint_type: str
    category: str
    isApproved: bool
    is_approved: bool
    approvalStatus: str
    approval_status: str
    confidence: float
    totalCalls: int
    total_calls: int
    bytesTransferred: int
    bytes_transferred: int
    dataTransferred: str
    data_transferred: str
    riskLevel: str
    risk_level: str
    riskScore: int
    risk_score: int
    reasons: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    detectionSignatures: List[str] = Field(default_factory=list)
    detection_signatures: List[str] = Field(default_factory=list)
    firstSeenAt: Optional[datetime] = None
    first_seen_at: Optional[datetime] = None
    lastSeenAt: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    investigationStatus: str = "active"
    investigation_status: str = "active"


class EndpointDetailResponse(EndpointInventoryItemResponse):
    """Detailed view of an individual AI endpoint record."""
    allowedSubnets: List[str] = Field(default_factory=list)
    observedModels: List[str] = Field(default_factory=list)
    dataClassification: Optional[str] = "Confidential / Intellectual Property"
    explanation: Optional[str] = None
    riskExplanation: Optional[str] = None
    notes: Optional[str] = None


class RiskAssessmentResponse(BaseModel):
    """Schema for individual risk finding matching frontend contract."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    target: str
    provider: str
    endpoint: str
    endpointHostname: str
    endpoint_hostname: str
    riskScore: int
    risk_score: int
    riskLevel: str
    risk_level: str
    isApproved: bool
    is_approved: bool
    approvalStatus: str
    approval_status: str
    policyRule: str
    policy_rule: str
    description: str
    reasons: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    firstSeenAt: Optional[datetime] = None
    first_seen_at: Optional[datetime] = None
    assessedAt: Optional[datetime] = None
    assessed_at: Optional[datetime] = None
    investigationStatus: str = "new"
    investigation_status: str = "new"
    status: str = "open"


class TestEvaluationMetricsResponse(BaseModel):
    """Schema for test reports and detection accuracy benchmarks."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    totalEvaluations: int = Field(0, description="Total evaluation test runs conducted")
    datasetSize: int = Field(0, description="Size of evaluation dataset records analyzed")
    evaluatedRecordsCount: int = Field(0, description="Count of evaluated records")
    precision: float = Field(1.0, description="AI traffic detection precision (0.0 to 1.0)")
    detectionPrecision: float = Field(1.0, description="Detection precision alias")
    recall: float = Field(1.0, description="AI traffic detection recall (0.0 to 1.0)")
    detectionRecall: float = Field(1.0, description="Detection recall alias")
    falsePositiveRate: float = Field(0.0, description="False positive rate (0.0 to 1.0)")
    fpr: float = Field(0.0, description="False positive rate alias")
    providerAccuracy: float = Field(1.0, description="Provider classification accuracy (0.0 to 1.0)")
    providerIdentificationAccuracy: float = Field(1.0, description="Provider identification accuracy alias")
    detectionAccuracy: float = Field(1.0, description="Overall detection accuracy")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evaluatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    categoriesBreakdown: Dict[str, int] = Field(default_factory=dict)

