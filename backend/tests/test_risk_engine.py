import pytest
from app.services.risk_engine import (
    EndpointTrafficAggregate,
    RiskEngine,
    score_to_severity,
    RISK_THRESHOLD_MEDIUM,
    RISK_THRESHOLD_HIGH,
    RISK_THRESHOLD_CRITICAL,
)


def test_score_to_severity_thresholds_and_boundaries():
    """Verify exact severity band classification immediately below, at, and above each threshold."""
    # Threshold 30: Low -> Medium
    assert score_to_severity(0) == "low"
    assert score_to_severity(29) == "low"
    assert score_to_severity(30) == "medium"
    assert score_to_severity(31) == "medium"

    # Threshold 60: Medium -> High
    assert score_to_severity(59) == "medium"
    assert score_to_severity(60) == "high"
    assert score_to_severity(61) == "high"

    # Threshold 80: High -> Critical
    assert score_to_severity(79) == "high"
    assert score_to_severity(80) == "critical"
    assert score_to_severity(81) == "critical"
    assert score_to_severity(100) == "critical"

    # Out of bounds clamping [0, 100]
    assert score_to_severity(-15) == "low"
    assert score_to_severity(150) == "critical"


def test_approved_ai_provider_generates_low_risk():
    """Approved enterprise AI provider with low traffic stays low risk without findings."""
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
    assert inv_item.risk_score == 0
    assert inv_item.risk_level == "low"
    assert finding is None
    assert inv_item.confidence == 0.99  # Confidence is distinct from risk


def test_approved_ai_provider_with_high_egress_triggers_medium_finding():
    """Approved enterprise AI provider with heavy data egress reaches medium risk and triggers finding."""
    engine = RiskEngine(approved_providers=["OpenAI"])
    agg = EndpointTrafficAggregate(
        target="api.openai.com",
        provider="OpenAI",
        category="LLM API / Foundation Models",
        total_calls=2,  # +10 points
        bytes_sent=60000,  # 50KB-100KB: +20 points
        bytes_received=80000,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert inv_item.is_approved is True
    assert inv_item.risk_score == 30  # 10 + 20 = 30
    assert inv_item.risk_level == "medium"
    assert finding is not None
    assert finding.risk_score == 30
    assert finding.risk_level == "medium"
    assert "Approved" in finding.policy_rule
    assert any("egress" in r.lower() for r in finding.reasons)


def test_unapproved_ai_provider_baseline_medium():
    """Unapproved provider with 1 call and small payload starts at score 50 (medium severity)."""
    engine = RiskEngine(approved_providers=["OpenAI"])
    agg = EndpointTrafficAggregate(
        target="api.mistral.ai",
        provider="Mistral",
        category="LLM API / Foundation Models",
        total_calls=1,
        bytes_sent=5000,
        bytes_received=12000,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert inv_item.is_approved is False
    assert inv_item.approval_status == "unapproved"
    assert inv_item.risk_score == 50
    assert inv_item.risk_level == "medium"
    assert finding is not None
    assert finding.risk_score == 50
    assert finding.risk_level == "medium"
    assert "POLICY-AI-01" in finding.policy_rule


def test_unapproved_ai_provider_high_severity():
    """Unapproved provider with moderate egress reaches score 60 (high severity)."""
    engine = RiskEngine(approved_providers=["OpenAI"])
    agg = EndpointTrafficAggregate(
        target="api.cohere.com",
        provider="Cohere",
        category="Enterprise AI & Embeddings",
        total_calls=1,
        bytes_sent=25000,  # 20KB-50KB: +10 points -> 50 + 10 = 60
        bytes_received=15000,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert inv_item.is_approved is False
    assert inv_item.risk_score == 60
    assert inv_item.risk_level == "high"
    assert finding is not None
    assert finding.risk_score == 60
    assert finding.risk_level == "high"


def test_unapproved_ai_provider_generates_critical_risk_finding():
    """Unapproved shadow AI provider with massive egress and repeat sessions reaches critical severity."""
    engine = RiskEngine(approved_providers=["OpenAI"])
    agg = EndpointTrafficAggregate(
        target="api.anthropic.com",
        provider="Anthropic",
        category="LLM API / Foundation Models",
        total_calls=2,  # +10 points
        bytes_sent=120000,  # >100KB: +30 points -> 50 + 10 + 30 = 90
        bytes_received=108000,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert inv_item.is_approved is False
    assert inv_item.approval_status == "unapproved"
    assert inv_item.risk_score == 90
    assert inv_item.risk_level == "critical"

    assert finding is not None
    assert finding.is_approved is False
    assert finding.provider == "Anthropic"
    assert finding.risk_score == 90
    assert finding.risk_level == "critical"
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
    assert inv_item.risk_score == 0
    assert finding is None


def test_confidence_remains_separate_from_risk():
    """Detection confidence is an indicator of classifier certainty, not threat severity."""
    engine = RiskEngine(approved_providers=["OpenAI"])

    agg_low = EndpointTrafficAggregate(
        target="api.openai.com",
        provider="OpenAI",
        category="LLM API / Foundation Models",
        total_calls=1,
        bytes_sent=1000,
    )
    inv_low, _ = engine.evaluate_endpoint(agg_low)

    agg_critical = EndpointTrafficAggregate(
        target="api.anthropic.com",
        provider="Anthropic",
        category="LLM API / Foundation Models",
        total_calls=5,
        bytes_sent=150000,
    )
    inv_critical, _ = engine.evaluate_endpoint(agg_critical)

    # Both have high signature detection confidence
    assert inv_low.confidence == 0.99
    assert inv_critical.confidence == 0.99

    # But their risk profiles are entirely separate
    assert inv_low.risk_level == "low"
    assert inv_low.risk_score == 0
    assert inv_critical.risk_level == "critical"
    assert inv_critical.risk_score >= 80


def test_contributing_factors_and_explanation_returned():
    """Verify structured contributing factors and human-readable explanation are populated."""
    engine = RiskEngine(approved_providers=["OpenAI"])
    agg = EndpointTrafficAggregate(
        target="api.anthropic.com",
        provider="Anthropic",
        category="LLM API / Foundation Models",
        total_calls=3,
        bytes_sent=75000,
        bytes_received=20000,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert len(inv_item.contributing_factors) >= 3
    assert inv_item.explanation is not None
    assert "Score" in inv_item.explanation
    assert "POLICY-AI-01" in inv_item.explanation

    assert finding is not None
    assert finding.risk_explanation == inv_item.explanation
    factor_names = {f["factor"] for f in finding.contributing_factors}
    assert "Policy Compliance" in factor_names
    assert "Data Egress Volume" in factor_names
    assert "Session Frequency" in factor_names
