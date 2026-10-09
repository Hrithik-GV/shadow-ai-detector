import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnalysisStatus(str, PyEnum):
    """Status states for a traffic analysis task."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TrafficAnalysis(Base):
    """Represents a traffic analysis run corresponding to an ingested capture file."""
    __tablename__ = "traffic_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_format: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # e.g., 'pcap', 'csv', 'json', 'netflow'
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status_enum", native_enum=False),
        default=AnalysisStatus.PENDING,
        nullable=False,
        index=True,
    )
    total_rows_received: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    valid_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    rejected_rows: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    error_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # One-to-many relationship with cascading delete
    records: Mapped[List["TrafficRecord"]] = relationship(
        "TrafficRecord",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="TrafficRecord.timestamp",
    )
    inventory_items: Mapped[List["AIEndpointInventoryModel"]] = relationship(
        "AIEndpointInventoryModel",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    risk_findings: Mapped[List["RiskFindingModel"]] = relationship(
        "RiskFindingModel",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4())
        kwargs.setdefault("status", AnalysisStatus.PENDING)
        kwargs.setdefault("total_rows_received", 0)
        kwargs.setdefault("valid_rows", 0)
        kwargs.setdefault("rejected_rows", 0)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<TrafficAnalysis(id={self.id}, filename='{self.original_filename}', status='{self.status}')>"


class TrafficRecord(Base):
    """Represents an individual traffic flow or event record extracted from an analysis run."""
    __tablename__ = "traffic_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("traffic_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    source_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
    )
    destination_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
    )
    destination_domain: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    destination_port: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    protocol: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )  # TCP, UDP, TLS, HTTP, etc.
    bytes_sent: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )
    bytes_received: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # Format-specific metadata justifiable for network capture analysis
    http_method: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    http_uri: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    http_status_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sni_hostname: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )  # TLS Server Name Indication header

    # Many-to-one relationship back to the parent analysis
    analysis: Mapped["TrafficAnalysis"] = relationship(
        "TrafficAnalysis",
        back_populates="records",
    )

    __table_args__ = (
        Index("ix_traffic_records_analysis_timestamp", "analysis_id", "timestamp"),
        Index("ix_traffic_records_domain_timestamp", "destination_domain", "timestamp"),
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4())
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<TrafficRecord(id={self.id}, analysis_id={self.analysis_id}, dest='{self.destination_domain or self.destination_ip}')>"


class AIEndpointInventoryModel(Base):
    """Represents a discovered and cataloged AI service endpoint in the inventory."""
    __tablename__ = "ai_endpoint_inventory"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("traffic_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(100), index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    hostname: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(512))
    endpoint_address: Mapped[str] = mapped_column(String(255))
    endpoint_type: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(100))
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    approval_status: Mapped[str] = mapped_column(String(50), default="unapproved", index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.99)
    total_calls: Mapped[int] = mapped_column(Integer, default=1)
    bytes_transferred: Mapped[int] = mapped_column(BigInteger, default=0)
    data_transferred: Mapped[str] = mapped_column(String(50), default="0 B")
    risk_level: Mapped[str] = mapped_column(String(20), default="low", index=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    reasons: Mapped[List[str]] = mapped_column(JSON, default=list)
    evidence: Mapped[List[str]] = mapped_column(JSON, default=list)
    detection_signatures: Mapped[List[str]] = mapped_column(JSON, default=list)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    investigation_status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    analysis: Mapped["TrafficAnalysis"] = relationship(
        "TrafficAnalysis",
        back_populates="inventory_items",
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4())
        super().__init__(**kwargs)


class RiskFindingModel(Base):
    """Represents an actionable security or policy risk finding produced by the Risk Engine."""
    __tablename__ = "risk_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("traffic_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(64), index=True)
    target: Mapped[str] = mapped_column(String(255), index=True)
    provider: Mapped[str] = mapped_column(String(100), index=True)
    endpoint: Mapped[str] = mapped_column(String(255))
    endpoint_hostname: Mapped[str] = mapped_column(String(255))
    risk_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    approval_status: Mapped[str] = mapped_column(String(50), default="unapproved")
    policy_rule: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    reasons: Mapped[List[str]] = mapped_column(JSON, default=list)
    evidence: Mapped[List[str]] = mapped_column(JSON, default=list)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    investigation_status: Mapped[str] = mapped_column(String(50), default="new")
    status: Mapped[str] = mapped_column(String(50), default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    analysis: Mapped["TrafficAnalysis"] = relationship(
        "TrafficAnalysis",
        back_populates="risk_findings",
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4())
        super().__init__(**kwargs)
