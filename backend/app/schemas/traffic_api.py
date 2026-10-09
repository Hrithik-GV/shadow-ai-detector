from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.traffic import RecordValidationError


class TrafficMetricsSummary(BaseModel):
    """Aggregate metrics derived strictly from actual processed/persisted traffic records."""
    model_config = ConfigDict(from_attributes=True)

    total_valid_records: int = Field(..., description="Count of valid traffic records in this analysis")
    total_bytes_sent: int = Field(0, description="Sum of bytes sent across all valid records")
    total_bytes_received: int = Field(0, description="Sum of bytes received across all valid records")
    unique_source_ips: int = Field(0, description="Number of distinct source IP addresses observed")
    unique_destination_domains: int = Field(0, description="Number of distinct destination domains observed")
    unique_destination_ips: int = Field(0, description="Number of distinct destination IP addresses observed")
    protocols: List[str] = Field(default_factory=list, description="List of network protocols observed")
    earliest_timestamp: Optional[datetime] = Field(None, description="Earliest event timestamp")
    latest_timestamp: Optional[datetime] = Field(None, description="Latest event timestamp")


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
