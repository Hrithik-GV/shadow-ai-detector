import pytest
from app.services.ai_detector import AIDetector, default_detector


def test_ai_detector_identifies_known_providers():
    """Verify AI detector identifies confirmed AI providers with high confidence."""
    detector = default_detector

    res_openai = detector.classify_target(domain="api.openai.com")
    assert res_openai.is_ai is True
    assert res_openai.is_uncertain is False
    assert res_openai.provider == "OpenAI"
    assert res_openai.confidence > 0.9

    res_anthropic = detector.classify_target(domain="api.anthropic.com")
    assert res_anthropic.is_ai is True
    assert res_anthropic.provider == "Anthropic"


def test_ai_detector_handles_unknown_domains_as_uncertain():
    """Unknown domains are handled as uncertain rather than automatically treated as AI."""
    detector = default_detector

    res_test = detector.classify_target(domain="unverified-ai-test.invalid")
    assert res_test.is_ai is False
    assert res_test.is_uncertain is True
    assert res_test.confidence == 0.0
    assert "uncertain" in res_test.classification.lower()


def test_ai_detector_handles_standard_domains_as_non_ai():
    """Standard non-AI web traffic is classified as standard traffic with zero confidence."""
    detector = default_detector

    res_example = detector.classify_target(domain="example.com")
    assert res_example.is_ai is False
    assert res_example.is_uncertain is False
    assert res_example.provider is None

    res_google = detector.classify_target(domain="google.com")
    assert res_google.is_ai is False
    assert res_google.is_uncertain is False
