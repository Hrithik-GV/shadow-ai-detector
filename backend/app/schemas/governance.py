from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


def sanitize_domain_signature(domain: str) -> str:
    """Sanitizes domain signature input by stripping protocol, path, and port."""
    cleaned = domain.strip().lower()
    if cleaned.startswith("http://"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("https://"):
        cleaned = cleaned[8:]
    cleaned = cleaned.split("/")[0].split(":")[0]
    return cleaned


class PolicyCreateRequest(BaseModel):
    """Payload to create a new AI governance policy."""
    provider_name: str = Field(..., min_length=2, max_length=100, description="Name of the AI provider (e.g. 'Anthropic', 'OpenAI')")
    domain_signatures: List[str] = Field(default_factory=list, description="List of authoritative domain or host signatures for the provider")
    approval_status: str = Field("approved", description="Approval verdict: 'approved', 'unapproved', or 'blocked'")
    is_enabled: bool = Field(True, description="Whether this policy rule is active")
    policy_rule: Optional[str] = Field(None, max_length=255, description="Rule code or descriptive tag (e.g. 'POLICY-AI-00: Approved Enterprise Provider')")
    description: Optional[str] = Field(None, max_length=1000, description="Business justification or policy details")

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Provider name must be at least 2 characters.")
        return cleaned

    @field_validator("approval_status")
    @classmethod
    def validate_approval_status(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ["approved", "unapproved", "blocked", "restricted"]:
            raise ValueError("Approval status must be one of: 'approved', 'unapproved', 'blocked', 'restricted'.")
        return cleaned

    @field_validator("domain_signatures")
    @classmethod
    def validate_domain_signatures(cls, v: List[str]) -> List[str]:
        cleaned_list: List[str] = []
        for d in v:
            sanitized = sanitize_domain_signature(d)
            if sanitized and sanitized not in cleaned_list:
                cleaned_list.append(sanitized)
        return cleaned_list


class PolicyUpdateRequest(BaseModel):
    """Payload to update an existing AI governance policy."""
    provider_name: Optional[str] = Field(None, min_length=2, max_length=100)
    domain_signatures: Optional[List[str]] = Field(None)
    approval_status: Optional[str] = Field(None)
    is_enabled: Optional[bool] = Field(None)
    policy_rule: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if len(cleaned) < 2:
                raise ValueError("Provider name must be at least 2 characters.")
            return cleaned
        return None

    @field_validator("approval_status")
    @classmethod
    def validate_approval_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if cleaned not in ["approved", "unapproved", "blocked", "restricted"]:
                raise ValueError("Approval status must be one of: 'approved', 'unapproved', 'blocked', 'restricted'.")
            return cleaned
        return None

    @field_validator("domain_signatures")
    @classmethod
    def validate_domain_signatures(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            cleaned_list: List[str] = []
            for d in v:
                sanitized = sanitize_domain_signature(d)
                if sanitized and sanitized not in cleaned_list:
                    cleaned_list.append(sanitized)
            return cleaned_list
        return None


class PolicyStatusUpdateRequest(BaseModel):
    """Quick payload to toggle approval status of a policy."""
    approval_status: str = Field(..., description="Target status: 'approved' or 'unapproved'")
    notes: Optional[str] = Field(None, description="Optional administrative rationale")

    @field_validator("approval_status")
    @classmethod
    def validate_approval_status(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ["approved", "unapproved", "blocked", "restricted"]:
            raise ValueError("Approval status must be one of: 'approved', 'unapproved', 'blocked', 'restricted'.")
        return cleaned


class PolicyResponse(BaseModel):
    """Schema representing an individual AI governance policy item."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    externalId: str = ""
    external_id: str = ""
    providerName: str = ""
    provider_name: str = ""
    domainSignatures: List[str] = Field(default_factory=list)
    domain_signatures: List[str] = Field(default_factory=list)
    approvalStatus: str = "approved"
    approval_status: str = "approved"
    isApproved: bool = False
    is_approved: bool = False
    isEnabled: bool = True
    is_enabled: bool = True
    policyRule: str = ""
    policy_rule: str = ""
    description: Optional[str] = None
    createdBy: Optional[str] = None
    created_by: Optional[str] = None
    updatedBy: Optional[str] = None
    updated_by: Optional[str] = None
    createdAt: datetime
    created_at: datetime
    updatedAt: datetime
    updated_at: datetime


class PolicyAuditLogResponse(BaseModel):
    """Schema representing an audit log entry for a policy change."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    policyId: Optional[uuid.UUID] = None
    policy_id: Optional[uuid.UUID] = None
    action: str
    providerName: str = ""
    provider_name: str = ""
    previousState: Optional[Dict[str, Any]] = None
    previous_state: Optional[Dict[str, Any]] = None
    newState: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    performedBy: str = ""
    performed_by: str = ""
    details: Optional[str] = None
    timestamp: datetime


class PolicySummaryMetricsResponse(BaseModel):
    """Summary overview metrics of the enterprise AI governance policies."""
    model_config = ConfigDict(from_attributes=True)

    totalPolicies: int = 0
    total_policies: int = 0
    approvedPolicies: int = 0
    approved_policies: int = 0
    unapprovedPolicies: int = 0
    unapproved_policies: int = 0
    disabledPolicies: int = 0
    disabled_policies: int = 0
    activeApprovedProviders: List[str] = Field(default_factory=list)
    active_approved_providers: List[str] = Field(default_factory=list)
