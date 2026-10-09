from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
import logging

from app.core.config import settings
from app.services.provider_registry import AIProviderRegistry, default_registry

logger = logging.getLogger(__name__)


@dataclass
class EndpointTrafficAggregate:
    """Aggregated traffic metrics for a single observed AI endpoint/domain."""
    target: str
    provider: str
    category: str
    total_calls: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    source_ips: List[str] = field(default_factory=list)
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    detection_signatures: List[str] = field(default_factory=list)


@dataclass
class EvaluatedRiskFinding:
    """Actionable security finding generated for an AI endpoint under organizational policy."""
    id: str
    target: str
    provider: str
    endpoint: str
    endpoint_hostname: str
    risk_score: int
    risk_level: str  # 'low' | 'medium' | 'high' | 'critical'
    is_approved: bool
    approval_status: str  # 'approved' | 'unapproved'
    policy_rule: str
    description: str
    reasons: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    first_seen_at: Optional[datetime] = None
    assessed_at: Optional[datetime] = None
    investigation_status: str = "new"
    status: str = "open"


@dataclass
class EvaluatedEndpointInventory:
    """Inventory record for a detected AI service endpoint."""
    id: str
    provider: str
    domain: str
    hostname: str
    url: str
    endpoint_address: str
    endpoint_type: str
    category: str
    is_approved: bool
    approval_status: str
    confidence: float
    total_calls: int
    bytes_transferred: int
    data_transferred: str
    risk_level: str
    risk_score: int
    reasons: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    detection_signatures: List[str] = field(default_factory=list)
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    investigation_status: str = "active"


class RiskEngine:
    """Evaluates detected AI endpoints against organizational cybersecurity and compliance policies."""

    def __init__(
        self,
        approved_providers: Optional[List[str]] = None,
        registry: Optional[AIProviderRegistry] = None,
    ) -> None:
        self.registry = registry or default_registry
        self.approved_providers = (
            approved_providers
            if approved_providers is not None
            else list(settings.APPROVED_AI_PROVIDERS)
        )

    def evaluate_endpoint(
        self,
        agg: EndpointTrafficAggregate,
    ) -> tuple[EvaluatedEndpointInventory, Optional[EvaluatedRiskFinding]]:
        """Evaluates an aggregated AI endpoint and determines risk score, level, and findings."""
        is_approved = self.registry.is_provider_approved(
            agg.provider,
            self.approved_providers,
        )
        approval_status = "approved" if is_approved else "unapproved"

        score = 0
        reasons: List[str] = []
        evidence: List[str] = [
            f"Destination Endpoint: {agg.target}",
            f"Resolved AI Provider: {agg.provider} ({agg.category})",
            f"Total Observed Sessions: {agg.total_calls}",
            f"Total Data Egress: {agg.bytes_sent:,} bytes sent, {agg.bytes_received:,} bytes received",
        ]
        if agg.source_ips:
            unique_sources = list(set(agg.source_ips))[:5]
            evidence.append(f"Originating Internal Host(s): {', '.join(unique_sources)}")

        # 1. Organizational Policy Compliance Rule
        if not is_approved:
            # High risk baseline: Unapproved Shadow AI usage
            score += 45
            reasons.append(
                f"Unapproved shadow AI service: '{agg.provider}' is not listed in the approved organizational AI registry."
            )
            policy_rule = "POLICY-AI-01: Unapproved Shadow AI Provider"
            description = (
                f"Unauthorized shadow AI provider '{agg.provider}' observed at '{agg.target}'. "
                f"Access violates organizational AI governance policy."
            )
        else:
            reasons.append(f"Authorized enterprise AI service: '{agg.provider}' is approved for business use.")
            policy_rule = "POLICY-AI-00: Approved Enterprise AI Service"
            description = f"Authorized AI provider '{agg.provider}' observed at '{agg.target}'."

        # 2. Data Egress Volume Rule (Prompt Injection / Sensitive Data Leakage Risk)
        if agg.bytes_sent > 100_000:
            score += 35
            reasons.append(
                f"Massive data egress ({agg.bytes_sent:,} bytes sent): potential large-scale document or source code upload."
            )
        elif agg.bytes_sent > 50_000:
            score += 25
            reasons.append(
                f"High data egress volume ({agg.bytes_sent:,} bytes sent): prompt payload exfiltration risk."
            )
        elif agg.bytes_sent > 20_000:
            score += 15
            reasons.append(
                f"Moderate data egress volume ({agg.bytes_sent:,} bytes sent)."
            )

        # 3. Connection Frequency / Persistence Rule
        if agg.total_calls > 1:
            score += 10
            reasons.append(
                f"Repeated AI endpoint observations ({agg.total_calls} interactions detected across capture period)."
            )

        # Final Score & Risk Level Classification
        total_score = min(100, max(0, score))
        if not is_approved:
            if total_score >= 80 or agg.bytes_sent > 100_000:
                risk_level = "critical"
            else:
                risk_level = "high"
        else:
            if total_score >= 60:
                risk_level = "medium"
            else:
                risk_level = "low"

        # Format Human-readable Data Transferred
        total_bytes = agg.bytes_sent + agg.bytes_received
        if total_bytes >= 1024 * 1024:
            data_transferred_str = f"{total_bytes / (1024 * 1024):.1f} MB"
        elif total_bytes >= 1024:
            data_transferred_str = f"{total_bytes / 1024:.1f} KB"
        else:
            data_transferred_str = f"{total_bytes} B"

        endpoint_id = f"EP-{uuid.uuid5(uuid.NAMESPACE_DNS, agg.target).hex[:12].upper()}"
        finding_id = f"RISK-{uuid.uuid5(uuid.NAMESPACE_DNS, f'risk-{agg.target}').hex[:12].upper()}"
        assessed_now = datetime.now(timezone.utc)

        # Create Inventory Record
        inventory_item = EvaluatedEndpointInventory(
            id=endpoint_id,
            provider=agg.provider,
            domain=agg.target,
            hostname=agg.target,
            url=f"https://{agg.target}",
            endpoint_address=agg.target,
            endpoint_type=agg.category,
            category=agg.category,
            is_approved=is_approved,
            approval_status=approval_status,
            confidence=0.99,
            total_calls=agg.total_calls,
            bytes_transferred=total_bytes,
            data_transferred=data_transferred_str,
            risk_level=risk_level,
            risk_score=total_score,
            reasons=list(reasons),
            evidence=list(evidence),
            detection_signatures=list(agg.detection_signatures),
            first_seen_at=agg.first_seen_at or assessed_now,
            last_seen_at=agg.last_seen_at or assessed_now,
            investigation_status="active",
        )

        # Create Risk Finding if unapproved or elevated risk
        finding: Optional[EvaluatedRiskFinding] = None
        if not is_approved or total_score >= 40:
            finding = EvaluatedRiskFinding(
                id=finding_id,
                target=agg.target,
                provider=agg.provider,
                endpoint=agg.target,
                endpoint_hostname=agg.target,
                risk_score=total_score,
                risk_level=risk_level,
                is_approved=is_approved,
                approval_status=approval_status,
                policy_rule=policy_rule,
                description=description,
                reasons=list(reasons),
                evidence=list(evidence),
                first_seen_at=agg.first_seen_at or assessed_now,
                assessed_at=agg.last_seen_at or assessed_now,
                investigation_status="new",
                status="open",
            )

        return inventory_item, finding


default_risk_engine = RiskEngine()
