import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    JSON,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIGovernancePolicyModel(Base):
    """Represents a database-backed AI governance and approval policy."""
    __tablename__ = "ai_governance_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        unique=True,
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    domain_signatures: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    approval_status: Mapped[str] = mapped_column(
        String(50),
        default="approved",
        index=True,
        nullable=False,
    )  # 'approved' | 'unapproved' | 'blocked' | 'restricted'
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False,
    )
    policy_rule: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )  # e.g., 'POLICY-AI-00: Authorized Enterprise Provider'
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="admin",
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default="admin",
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

    __table_args__ = (
        Index("ix_ai_gov_policy_provider_enabled", "provider_name", "is_enabled"),
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4())
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<AIGovernancePolicy(id={self.id}, provider='{self.provider_name}', status='{self.approval_status}', enabled={self.is_enabled})>"


class PolicyAuditLogModel(Base):
    """Audit log recording administrative changes to AI governance policies."""
    __tablename__ = "policy_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # 'create' | 'update' | 'status_change' | 'disable' | 'delete'
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    previous_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    new_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    performed_by: Mapped[str] = mapped_column(
        String(100),
        default="admin",
        nullable=False,
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("id", uuid.uuid4())
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<PolicyAuditLog(action='{self.action}', provider='{self.provider_name}', performed_by='{self.performed_by}')>"
