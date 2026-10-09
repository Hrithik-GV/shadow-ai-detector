import pytest
from app.services.provider_registry import AIProviderRegistry, default_registry


def test_known_ai_domains_match_registry():
    """Verify known AI provider domains match authoritative registry entries."""
    registry = default_registry

    # OpenAI
    match = registry.match_domain("api.openai.com")
    assert match is not None
    assert match.name == "OpenAI"

    # Anthropic
    match = registry.match_domain("api.anthropic.com")
    assert match is not None
    assert match.name == "Anthropic"

    # Google
    match = registry.match_domain("generativelanguage.googleapis.com")
    assert match is not None
    assert match.name == "Google"

    # Microsoft Copilot
    match = registry.match_domain("copilot.microsoft.com")
    assert match is not None
    assert match.name == "Microsoft"


def test_standard_domains_do_not_match():
    """Verify standard non-AI web domains do NOT match AI registry."""
    registry = default_registry

    assert registry.match_domain("example.com") is None
    assert registry.match_domain("google.com") is None
    assert registry.match_domain("microsoft.com") is None


def test_unknown_test_domains_do_not_match():
    """Verify unknown test domains return None (handled as uncertain)."""
    registry = default_registry

    assert registry.match_domain("unverified-ai-test.invalid") is None
    assert registry.match_domain("unknown-domain.com") is None


def test_provider_approval_policy():
    """Verify approved vs unapproved provider resolution."""
    registry = default_registry
    approved = ["OpenAI", "Microsoft"]

    assert registry.is_provider_approved("OpenAI", approved) is True
    assert registry.is_provider_approved("Microsoft", approved) is True
    assert registry.is_provider_approved("Anthropic", approved) is False
    assert registry.is_provider_approved("Google", approved) is False
