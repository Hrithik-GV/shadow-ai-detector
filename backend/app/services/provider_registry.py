from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIProviderEntry:
    """Represents a cataloged AI service provider and its associated network indicators."""
    name: str
    category: str
    primary_domain: str
    domains: List[str]
    description: str
    detection_signatures: List[str] = field(default_factory=list)


# Registry of known AI providers and their authoritative network endpoints
KNOWN_AI_PROVIDERS: List[AIProviderEntry] = [
    AIProviderEntry(
        name="OpenAI",
        category="LLM API / Foundation Models",
        primary_domain="openai.com",
        domains=[
            "api.openai.com",
            "chatgpt.com",
            "openai.com",
            "platform.openai.com",
            "auth.openai.com",
            "oaistatic.com",
            "oaiusercontent.com",
        ],
        description="OpenAI generative models (GPT-4o, ChatGPT, OpenAI Embeddings & Whisper APIs).",
        detection_signatures=["OpenAI-API-Traffic", "ChatGPT-Web-Traffic"],
    ),
    AIProviderEntry(
        name="Anthropic",
        category="LLM API / Foundation Models",
        primary_domain="anthropic.com",
        domains=[
            "api.anthropic.com",
            "anthropic.com",
            "claude.ai",
            "console.anthropic.com",
        ],
        description="Anthropic Claude foundation models and API endpoints.",
        detection_signatures=["Anthropic-Claude-Traffic", "Claude-Web-Traffic"],
    ),
    AIProviderEntry(
        name="Google",
        category="LLM API / Foundation Models",
        primary_domain="generativelanguage.googleapis.com",
        domains=[
            "generativelanguage.googleapis.com",
            "gemini.google.com",
            "ai.google.dev",
            "vertexai.googleapis.com",
            "bard.google.com",
        ],
        description="Google Gemini and PaLM generative language API and web endpoints.",
        detection_signatures=["Google-Gemini-Traffic", "GenerativeLanguage-API"],
    ),
    AIProviderEntry(
        name="Microsoft",
        category="AI Assistant",
        primary_domain="copilot.microsoft.com",
        domains=[
            "copilot.microsoft.com",
            "sydney.bing.com",
            "edgeservices.bing.com",
        ],
        description="Microsoft Copilot generative AI assistant and enterprise endpoints.",
        detection_signatures=["Microsoft-Copilot-Traffic"],
    ),
    AIProviderEntry(
        name="Mistral",
        category="LLM API / Foundation Models",
        primary_domain="mistral.ai",
        domains=[
            "api.mistral.ai",
            "mistral.ai",
            "chat.mistral.ai",
            "console.mistral.ai",
        ],
        description="Mistral AI foundation models and Le Chat platform.",
        detection_signatures=["Mistral-AI-Traffic"],
    ),
    AIProviderEntry(
        name="Perplexity",
        category="AI Search Engine",
        primary_domain="perplexity.ai",
        domains=[
            "api.perplexity.ai",
            "perplexity.ai",
            "www.perplexity.ai",
        ],
        description="Perplexity AI conversational search and LLM inference API.",
        detection_signatures=["Perplexity-AI-Traffic"],
    ),
    AIProviderEntry(
        name="Cohere",
        category="LLM API / Foundation Models",
        primary_domain="cohere.com",
        domains=[
            "api.cohere.ai",
            "cohere.com",
            "cohere.ai",
        ],
        description="Cohere enterprise generative language and embedding models.",
        detection_signatures=["Cohere-API-Traffic"],
    ),
    AIProviderEntry(
        name="HuggingFace",
        category="Model Hub & Inference API",
        primary_domain="huggingface.co",
        domains=[
            "api-inference.huggingface.co",
            "huggingface.co",
            "hf.space",
        ],
        description="Hugging Face hosted open-source AI models and inference endpoints.",
        detection_signatures=["HuggingFace-Inference-Traffic"],
    ),
]


class AIProviderRegistry:
    """Registry engine providing domain resolution and organizational approval lookup for AI services."""

    def __init__(self, providers: Optional[List[AIProviderEntry]] = None) -> None:
        self.providers = providers if providers is not None else KNOWN_AI_PROVIDERS
        self._exact_domain_map: Dict[str, AIProviderEntry] = {}
        self._wildcard_domain_map: Dict[str, AIProviderEntry] = {}

        for entry in self.providers:
            for domain in entry.domains:
                d_lower = domain.strip().lower().rstrip(".")
                self._exact_domain_map[d_lower] = entry
                self._wildcard_domain_map[d_lower] = entry

    def match_domain(self, domain_or_host: Optional[str]) -> Optional[AIProviderEntry]:
        """Matches a domain, hostname, or SNI string against known AI provider signatures.
        
        Rules:
        - Case-insensitive, strips trailing dots and port numbers.
        - Matches exact registered domains first (e.g. 'api.openai.com').
        - Matches subdomain suffixes for registered base domains (e.g. 'sub.claude.ai' -> Anthropic).
        - Explicitly distinguishes multi-purpose tech domains (e.g. 'google.com' is not AI, 
          only 'generativelanguage.googleapis.com' is AI).
        - Returns None for unknown or general web domains (e.g. 'example.com', 'unverified-ai-test.invalid').
        """
        if not domain_or_host:
            return None

        clean_host = str(domain_or_host).strip().lower().rstrip(".")
        if ":" in clean_host:
            clean_host = clean_host.split(":")[0]

        # 1. Exact match against registered domains
        if clean_host in self._exact_domain_map:
            return self._exact_domain_map[clean_host]

        # 2. Subdomain match (e.g. foo.api.openai.com matches openai.com / api.openai.com)
        for registered_domain, entry in self._wildcard_domain_map.items():
            # Only perform suffix matching if the registered domain is an explicit domain (e.g. openai.com)
            # Avoid suffix matching on broad multi-service parent domains
            if clean_host.endswith("." + registered_domain):
                return entry

        return None

    def is_provider_approved(
        self,
        provider_name: str,
        approved_providers: Optional[List[str]] = None,
    ) -> bool:
        """Determines whether a detected AI provider is permitted under enterprise security policy."""
        if not approved_providers:
            return False

        normalized_approved = {p.strip().lower() for p in approved_providers if p and p.strip()}
        return provider_name.strip().lower() in normalized_approved

    def list_all_providers(self) -> List[AIProviderEntry]:
        """Returns the complete list of known AI provider signatures."""
        return list(self.providers)


# Global singleton instance
default_registry = AIProviderRegistry()
