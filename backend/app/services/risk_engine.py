from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
import logging

from app.core.config import settings
from app.services.provider_registry import AIProviderRegistry, default_registry

logger = logging.getLogger(__name__)

# Severity Thresholds (0-100 scale)
RISK_THRESHOLD_MEDIUM = 30
RISK_THRESHOLD_HIGH = 60
RISK_THRESHOLD_CRITICAL = 80


def score_to_severity(score: int) -> str:
    """Deterministic, unified mapping from numeric risk score (0-100) to severity band.

    Severity Bands:
      - Low:       0 <= score < 30   (0 to 29)
      - Medium:   30 <= score < 60   (30 to 59)
      - High:     60 <= score < 80   (60 to 79)
      - Critical: 80 <= score <= 100 (80 to 100)
    """
    clamped = max(0, min(100, int(score)))
    if clamped >= RISK_THRESHOLD_CRITICAL:
        return "critical"
    elif clamped >= RISK_THRESHOLD_HIGH:
        return "high"
    elif clamped >= RISK_THRESHOLD_MEDIUM:
        return "medium"
    else:
        return "low"


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
    evidence_sources: List[str] = field(default_factory=list)


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
    contributing_factors: List[Dict[str, Any]] = field(default_factory=list)
    explanation: Optional[str] = None
    risk_explanation: Optional[str] = None
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
    contributing_factors: List[Dict[str, Any]] = field(default_factory=list)
    explanation: Optional[str] = None
    risk_explanation: Optional[str] = None
    detection_signatures: List[str] = field(default_factory=list)
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    investigation_status: str = "active"


class RiskEngine:
    """Evaluates detected AI endpoints against organizational cybersecurity and compliance policies."""

    def __init__(
        self,
        approved_providers: Optional[List[str]] = None,
        blocked_providers: Optional[List[str]] = None,
        registry: Optional[AIProviderRegistry] = None,
        db: Optional[Any] = None,
    ) -> None:
        self.registry = registry or default_registry
        self.db = db
        self.blocked_providers = [p.strip() for p in (blocked_providers or [])]
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
        if self.db is not None:
            from app.services.policy_service import PolicyService
            is_approved, approval_status, resolved_policy_rule = PolicyService.resolve_effective_approval(
                self.db,
                provider_name=agg.provider,
                target_domain=agg.target,
            )
        else:
            # Deterministic conflict resolution: blocked strictly overrides approved
            is_blocked = any(
                b.lower() == agg.provider.lower() for b in self.blocked_providers
            )
            if is_blocked:
                is_approved = False
                approval_status = "blocked"
                resolved_policy_rule = "POLICY-AI-01: Prohibited Shadow AI Provider"
            else:
                is_approved = self.registry.is_provider_approved(
                    agg.provider,
                    self.approved_providers,
                )
                approval_status = "approved" if is_approved else "unapproved"
                resolved_policy_rule = (
                    "POLICY-AI-00: Approved Enterprise Provider"
                    if is_approved
                    else "POLICY-AI-01: Unapproved Shadow AI Provider"
                )

        raw_score = 0
        reasons: List[str] = []
        contributing_factors: List[Dict[str, Any]] = []
        evidence: List[str] = [
            f"Destination Endpoint: {agg.target}",
            f"Resolved AI Provider: {agg.provider} ({agg.category})",
            f"Total Observed Sessions: {agg.total_calls}",
            f"Total Data Egress: {agg.bytes_sent:,} bytes sent, {agg.bytes_received:,} bytes received",
        ]
        if agg.source_ips:
            unique_sources = list(set(agg.source_ips))[:5]
            evidence.append(f"Originating Internal Host(s): {', '.join(unique_sources)}")

        if agg.evidence_sources:
            source_labels = {
                "tls_sni": "TLS Server Name Indication (SNI) Handshake",
                "dns_correlation": "DNS Resolution Correlation (A/AAAA record)",
                "dns_query": "DNS Query Name Observation",
                "csv_direct": "Direct CSV Log Entry",
                "json_direct": "Direct JSON Log Entry",
                "ip_only": "Direct Network IP Observation (No Hostname)",
            }
            labels = [source_labels.get(s, s) for s in agg.evidence_sources]
            evidence.append(f"Evidence Provenance: {', '.join(labels)}")

            if any(s in ("tls_sni", "dns_correlation", "dns_query", "ip_only") for s in agg.evidence_sources):
                evidence.append(
                    "Measurement Basis: Wire bytes observed at network layer (IP packet total length). "
                    "Encrypted TLS payloads do not reveal prompt content or token counts."
                )

        # 1. Organizational Policy Compliance Rule
        if not is_approved:
            # Baseline unapproved Shadow AI policy violation
            policy_points = 50
            raw_score += policy_points
            policy_rule = resolved_policy_rule or "POLICY-AI-01: Unapproved Shadow AI Provider"
            reasons.append(
                f"Unapproved shadow AI service: '{agg.provider}' is not listed in the approved organizational AI registry."
            )
            contributing_factors.append({
                "factor": "Policy Compliance",
                "points": policy_points,
                "status": "violation",
                "description": f"Unapproved AI provider '{agg.provider}' violating organizational AI governance policy.",
            })
            description = (
                f"Unauthorized shadow AI provider '{agg.provider}' observed at '{agg.target}'. "
                f"Access violates organizational AI governance policy."
            )
        else:
            policy_points = 0
            policy_rule = resolved_policy_rule or "POLICY-AI-00: Approved Enterprise AI Service"
            reasons.append(f"Authorized enterprise AI service: '{agg.provider}' is approved for business use.")
            contributing_factors.append({
                "factor": "Policy Compliance",
                "points": 0,
                "status": "compliant",
                "description": f"Authorized AI provider '{agg.provider}' approved for business use.",
            })
            description = f"Authorized AI provider '{agg.provider}' observed at '{agg.target}'."


        # 2. Data Egress Volume Rule (Prompt Injection / Sensitive Data Leakage Risk)
        egress_points = 0
        if agg.bytes_sent > 100_000:
            egress_points = 30
            raw_score += egress_points
            reasons.append(
                f"Massive data egress ({agg.bytes_sent:,} bytes sent): elevated risk of large-scale document, database, or source code exfiltration."
            )
            contributing_factors.append({
                "factor": "Data Egress Volume",
                "points": egress_points,
                "tier": "massive (>100KB)",
                "bytes_sent": agg.bytes_sent,
                "description": "Massive outbound payload volume suggests document or codebase exfiltration.",
            })
        elif agg.bytes_sent > 50_000:
            egress_points = 20
            raw_score += egress_points
            reasons.append(
                f"High data egress volume ({agg.bytes_sent:,} bytes sent): substantial prompt payload or document transfer."
            )
            contributing_factors.append({
                "factor": "Data Egress Volume",
                "points": egress_points,
                "tier": "high (50KB-100KB)",
                "bytes_sent": agg.bytes_sent,
                "description": "Substantial outbound payload volume.",
            })
        elif agg.bytes_sent > 20_000:
            egress_points = 10
            raw_score += egress_points
            reasons.append(
                f"Moderate data egress volume ({agg.bytes_sent:,} bytes sent): multi-turn interaction."
            )
            contributing_factors.append({
                "factor": "Data Egress Volume",
                "points": egress_points,
                "tier": "moderate (20KB-50KB)",
                "bytes_sent": agg.bytes_sent,
                "description": "Moderate outbound payload volume.",
            })
        else:
            contributing_factors.append({
                "factor": "Data Egress Volume",
                "points": 0,
                "tier": "low (<=20KB)",
                "bytes_sent": agg.bytes_sent,
                "description": "Low outbound payload volume within expected telemetry baseline.",
            })

        # 3. Connection Frequency / Persistence Rule
        frequency_points = 0
        if agg.total_calls > 10:
            frequency_points = 20
            raw_score += frequency_points
            reasons.append(
                f"High-frequency interaction ({agg.total_calls} sessions observed): continuous workflow integration."
            )
            contributing_factors.append({
                "factor": "Session Frequency",
                "points": frequency_points,
                "total_calls": agg.total_calls,
                "description": "High-frequency interaction pattern across capture window.",
            })
        elif agg.total_calls > 1:
            frequency_points = 10
            raw_score += frequency_points
            reasons.append(
                f"Repeated AI endpoint observations ({agg.total_calls} interactions detected across capture period)."
            )
            contributing_factors.append({
                "factor": "Session Frequency",
                "points": frequency_points,
                "total_calls": agg.total_calls,
                "description": "Repeated interaction detected across capture window.",
            })
        else:
            contributing_factors.append({
                "factor": "Session Frequency",
                "points": 0,
                "total_calls": agg.total_calls,
                "description": "Single isolated interaction observed.",
            })

        # 4. Data Ingress / Response Volume Rule (Secondary)
        ingress_points = 0
        if agg.bytes_received > 500_000:
            ingress_points = 5
            raw_score += ingress_points
            reasons.append(
                f"High response payload volume ({agg.bytes_received:,} bytes received)."
            )
            contributing_factors.append({
                "factor": "Data Ingress Volume",
                "points": ingress_points,
                "bytes_received": agg.bytes_received,
                "description": "Substantial inbound payload volume.",
            })

        # Final Score: guaranteed [0, 100] clamp
        total_score = max(0, min(100, raw_score))

        # Severity band: strictly determined by total_score mapping
        risk_level = score_to_severity(total_score)

        # Build human-readable explanations
        factor_strs = [
            f"Policy (+{policy_points})",
            f"Egress (+{egress_points})",
            f"Frequency (+{frequency_points})",
        ]
        if ingress_points > 0:
            factor_strs.append(f"Ingress (+{ingress_points})")

        risk_explanation = (
            f"Score {total_score}/100 ({risk_level.upper()}) derived from: {', '.join(factor_strs)}. "
            f"Governing rule: {policy_rule}."
        )

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
        # Note: confidence is purely detection certainty (0.99 for signature match), separate from risk_level/score.
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
            contributing_factors=list(contributing_factors),
            explanation=risk_explanation,
            risk_explanation=risk_explanation,
            detection_signatures=list(agg.detection_signatures),
            first_seen_at=agg.first_seen_at or assessed_now,
            last_seen_at=agg.last_seen_at or assessed_now,
            investigation_status="active",
        )

        # Create Risk Finding if unapproved or elevated risk (score >= 30, Medium/High/Critical)
        finding: Optional[EvaluatedRiskFinding] = None
        if not is_approved or total_score >= RISK_THRESHOLD_MEDIUM:
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
                contributing_factors=list(contributing_factors),
                explanation=risk_explanation,
                risk_explanation=risk_explanation,
                first_seen_at=agg.first_seen_at or assessed_now,
                assessed_at=agg.last_seen_at or assessed_now,
                investigation_status="new",
                status="open",
            )

        return inventory_item, finding


default_risk_engine = RiskEngine()
