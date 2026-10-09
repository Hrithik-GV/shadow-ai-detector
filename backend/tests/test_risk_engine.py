import pytest
from app.services.risk_engine import EndpointTrafficAggregate, RiskEngine


def test_approved_ai_provider_generates_low_risk():
    """Approved enterprise AI provider does not trigger unapproved policy violation."""
    engine = RiskEngine(approved_providers=["OpenAI"])
    agg = EndpointTrafficAggregate(
        target="api.openai.com",
        provider="OpenAI",
        category="LLM API / Foundation Models",
        total_calls=1,
        bytes_sent=1500,
        bytes_received=4500,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert inv_item.is_approved is True
    assert inv_item.approval_status == "approved"
    assert inv_item.risk_level == "low"
    assert finding is None


def test_unapproved_ai_provider_generates_high_risk_finding():
    """Unapproved shadow AI provider generates a high/critical risk finding under policy."""
    engine = RiskEngine(approved_providers=["OpenAI"])
    agg = EndpointTrafficAggregate(
        target="api.anthropic.com",
        provider="Anthropic",
        category="LLM API / Foundation Models",
        total_calls=2,
        bytes_sent=120000,
        bytes_received=108000,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert inv_item.is_approved is False
    assert inv_item.approval_status == "unapproved"
    assert inv_item.risk_level in ["high", "critical"]
    assert inv_item.risk_score >= 75

    assert finding is not None
    assert finding.is_approved is False
    assert finding.provider == "Anthropic"
    assert "Unapproved" in finding.policy_rule
    assert any("shadow" in r.lower() or "unapproved" in r.lower() for r in finding.reasons)
    assert any("egress" in r.lower() for r in finding.reasons)


def test_custom_approved_provider_policy():
    """Adding Anthropic to approved list updates risk accordingly."""
    engine = RiskEngine(approved_providers=["OpenAI", "Anthropic"])
    agg = EndpointTrafficAggregate(
        target="api.anthropic.com",
        provider="Anthropic",
        category="LLM API / Foundation Models",
        total_calls=1,
        bytes_sent=5000,
        bytes_received=10000,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert inv_item.is_approved is True
    assert inv_item.approval_status == "approved"
    assert inv_item.risk_level == "low"
    assert finding is None
