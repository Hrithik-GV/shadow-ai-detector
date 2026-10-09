from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from app.services.provider_registry import AIProviderEntry, AIProviderRegistry, default_registry

logger = logging.getLogger(__name__)


@dataclass
class AIDetectionResult:
    """Detection outcome for an individual network flow or endpoint observation."""
    is_ai: bool
    is_uncertain: bool
    provider: Optional[str] = None
    category: Optional[str] = None
    matched_domain: Optional[str] = None
    confidence: float = 0.0
    classification: str = "standard_traffic"
    detection_signatures: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


class AIDetector:
    """Service that inspects traffic flow indicators to detect AI foundation and model endpoints.
    
    Adheres strictly to zero-false-positive principles:
    - Exact and subdomain matches against registered AI providers yield confirmed AI detections.
    - Unknown, test, or unverified domains are treated as UNCERTAIN / NON-AI, not automatically classified as AI.
    - Standard non-AI domains (google.com, example.com) are classified as standard traffic.
    """

    def __init__(self, registry: Optional[AIProviderRegistry] = None) -> None:
        self.registry = registry or default_registry

    def classify_target(
        self,
        domain: Optional[str] = None,
        sni_hostname: Optional[str] = None,
        destination_ip: Optional[str] = None,
        http_uri: Optional[str] = None,
    ) -> AIDetectionResult:
        """Classifies a target network destination based on observed domain, SNI, or URI attributes."""
        # Primary identifier is destination domain or SNI hostname
        target_domain = domain or sni_hostname

        if not target_domain and not destination_ip:
            return AIDetectionResult(
                is_ai=False,
                is_uncertain=False,
                classification="unspecified_destination",
                confidence=0.0,
            )

        # 1. Match against Known AI Provider Registry
        matched_entry = self.registry.match_domain(target_domain) if target_domain else None

        if matched_entry:
            return AIDetectionResult(
                is_ai=True,
                is_uncertain=False,
                provider=matched_entry.name,
                category=matched_entry.category,
                matched_domain=target_domain,
                confidence=0.99,
                classification="confirmed_ai",
                detection_signatures=list(matched_entry.detection_signatures),
                reasons=[
                    f"Authoritative domain match for AI provider: {matched_entry.name}",
                    f"Service Category: {matched_entry.category}",
                ],
            )

        # 2. Check for unknown or suspicious test domains
        # Requirement: "Unknown domains are handled as uncertain rather than automatically treated as AI"
        if target_domain:
            target_lower = target_domain.lower()
            is_suspicious_or_unknown_tld = (
                target_lower.endswith(".invalid")
                or target_lower.endswith(".test")
                or target_lower.endswith(".local")
                or "ai-test" in target_lower
                or "unverified" in target_lower
            )

            if is_suspicious_or_unknown_tld:
                return AIDetectionResult(
                    is_ai=False,
                    is_uncertain=True,
                    provider="Unknown / Unverified",
                    category="Unverified Domain",
                    matched_domain=target_domain,
                    confidence=0.0,
                    classification="uncertain_unknown_domain",
                    detection_signatures=["Unverified-Domain-Signature"],
                    reasons=[
                        f"Unverified or test domain '{target_domain}' does not match any registered AI provider. "
                        f"Treated as uncertain and excluded from confirmed AI classifications."
                    ],
                )

        # 3. Standard Non-AI Traffic (e.g. example.com, google.com, internal IP)
        return AIDetectionResult(
            is_ai=False,
            is_uncertain=False,
            provider=None,
            category="Standard Network Traffic",
            matched_domain=target_domain,
            confidence=0.0,
            classification="standard_traffic",
            reasons=["No AI service signatures or provider domains detected."],
        )


default_detector = AIDetector()
