import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.governance import AIGovernancePolicyModel, PolicyAuditLogModel
from app.services.policy_service import PolicyService
from app.services.risk_engine import EndpointTrafficAggregate, RiskEngine


ADMIN_HEADER = {"X-Admin-Token": settings.ADMIN_API_KEY}
BEARER_HEADER = {"Authorization": f"Bearer {settings.ADMIN_API_KEY}"}
INVALID_HEADER = {"X-Admin-Token": "invalid-token-12345"}


@pytest.fixture(autouse=True)
def cleanup_policies_after_test():
    yield
    from app.db.session import get_engine
    from sqlalchemy import text
    engine = get_engine()
    if engine:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM policy_audit_logs WHERE provider_name != 'OpenAI'"))
            conn.execute(text("DELETE FROM ai_governance_policies WHERE provider_name != 'OpenAI'"))
            conn.commit()


def test_list_policies_public_and_summary(client: TestClient, db_session: Session):
    """Policies list and summary can be retrieved without authentication."""
    response = client.get("/api/policies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    summary_res = client.get("/api/policies/summary")
    assert summary_res.status_code == 200
    data = summary_res.json()
    assert "totalPolicies" in data or "total_policies" in data


def test_create_policy_requires_authentication(client: TestClient):
    """Write operations without valid admin credentials fail with 401."""
    unique_provider = f"Unauth-{uuid.uuid4().hex[:6]}"
    payload = {
        "provider_name": unique_provider,
        "domain_signatures": ["api.testai.corp"],
        "approval_status": "approved",
    }
    # No auth
    res_no_auth = client.post("/api/policies", json=payload)
    assert res_no_auth.status_code == 401

    # Invalid auth
    res_invalid = client.post("/api/policies", json=payload, headers=INVALID_HEADER)
    assert res_invalid.status_code == 401


def test_create_policy_and_domain_sanitization(client: TestClient, db_session: Session):
    """Admin can create policy, and URL domains are properly sanitized to clean hostnames."""
    unique_provider = f"Cohere-{uuid.uuid4().hex[:6]}"
    payload = {
        "provider_name": unique_provider,
        "domain_signatures": ["https://api.cohere.ai:443/v1/generate", "cohere.com/pricing"],
        "approval_status": "approved",
        "policy_rule": "POLICY-AI-00: Approved Enterprise Provider",
        "description": "Authorized for semantic search and reranking workloads",
    }

    res = client.post("/api/policies", json=payload, headers=ADMIN_HEADER)
    assert res.status_code == 201
    created = res.json()
    assert created["providerName"] == unique_provider
    assert created["approvalStatus"] == "approved"
    assert created["isApproved"] is True
    # Verify sanitization stripped scheme, port, and paths
    assert "api.cohere.ai" in created["domainSignatures"]
    assert "cohere.com" in created["domainSignatures"]

    # Verify audit log was recorded in PostgreSQL
    policy_id = created["id"]
    audit_logs = client.get("/api/policies/audit-logs").json()
    assert any(log["action"] == "create" and log["providerName"] == unique_provider for log in audit_logs)


def test_prevent_duplicate_active_policy(client: TestClient, db_session: Session):
    """Creating a duplicate active policy for the same provider returns 409 Conflict."""
    unique_provider = f"Duplicate-{uuid.uuid4().hex[:6]}"
    payload = {
        "provider_name": unique_provider,
        "domain_signatures": ["duplicate.ai"],
        "approval_status": "approved",
    }
    res1 = client.post("/api/policies", json=payload, headers=ADMIN_HEADER)
    assert res1.status_code == 201

    # Attempt second active policy with identical provider name
    res2 = client.post("/api/policies", json=payload, headers=ADMIN_HEADER)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_update_policy_and_bearer_auth(client: TestClient, db_session: Session):
    """Policies can be updated using Bearer token authentication."""
    unique_provider = f"Claude-{uuid.uuid4().hex[:6]}"
    # Create initial policy
    create_payload = {
        "provider_name": unique_provider,
        "domain_signatures": ["claude.ai", "anthropic.com"],
        "approval_status": "unapproved",
        "description": "Pending internal compliance review",
    }
    create_res = client.post("/api/policies", json=create_payload, headers=ADMIN_HEADER)
    assert create_res.status_code == 201
    policy_id = create_res.json()["id"]

    # Update using Authorization: Bearer
    update_payload = {
        "approval_status": "approved",
        "description": "Compliance review passed, enterprise license active",
    }
    update_res = client.put(f"/api/policies/{policy_id}", json=update_payload, headers=BEARER_HEADER)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["approvalStatus"] == "approved"
    assert updated["isApproved"] is True
    assert "Compliance review passed" in updated["description"]


def test_quick_status_toggle_and_disable_policy(client: TestClient, db_session: Session):
    """Admin can quickly toggle approval status or disable a policy safely."""
    unique_provider = f"Toggle-{uuid.uuid4().hex[:6]}"
    create_res = client.post(
        "/api/policies",
        json={
            "provider_name": unique_provider,
            "domain_signatures": ["toggle.ai"],
            "approval_status": "approved",
        },
        headers=ADMIN_HEADER,
    )
    assert create_res.status_code == 201
    policy_id = create_res.json()["id"]

    # Quick toggle to unapproved / blocked
    status_res = client.patch(
        f"/api/policies/{policy_id}/status",
        json={"approval_status": "blocked", "notes": "Emergency security revocation"},
        headers=ADMIN_HEADER,
    )
    assert status_res.status_code == 200
    assert status_res.json()["approvalStatus"] == "blocked"
    assert status_res.json()["isApproved"] is False

    # Disable policy safely
    disable_res = client.post(f"/api/policies/{policy_id}/disable", headers=ADMIN_HEADER)
    assert disable_res.status_code == 200
    assert disable_res.json()["isEnabled"] is False


def test_deterministic_conflict_precedence_unapproved_wins(db_session: Session):
    """Deterministic precedence: when active policies conflict, unapproved/blocked strictly overrides approved."""
    unique_provider = f"Conflicted-{uuid.uuid4().hex[:6]}"
    # Create conflicting policies in DB for the same provider
    pol_approved = AIGovernancePolicyModel(
        external_id=f"POL-{uuid.uuid4().hex[:8].upper()}",
        provider_name=unique_provider,
        domain_signatures=["api.conflicted.ai"],
        approval_status="approved",
        is_enabled=True,
        policy_rule="POLICY-AI-00: Approved Enterprise Provider",
    )
    pol_blocked = AIGovernancePolicyModel(
        external_id=f"POL-{uuid.uuid4().hex[:8].upper()}",
        provider_name=unique_provider,
        domain_signatures=["api.conflicted.ai"],
        approval_status="blocked",
        is_enabled=True,
        policy_rule="POLICY-AI-01: Prohibited Shadow AI Provider",
    )
    db_session.add(pol_approved)
    db_session.add(pol_blocked)
    db_session.flush()

    # Evaluation MUST resolve to unapproved / false
    is_approved, status_str, rule_str = PolicyService.resolve_effective_approval(
        db=db_session,
        provider_name=unique_provider,
        target_domain="api.conflicted.ai",
    )
    assert is_approved is False
    assert status_str in ["blocked", "unapproved"]
    assert "POLICY-AI-01" in rule_str

    # Effective approved providers list MUST NOT include ConflictedAI
    effective_approved = PolicyService.get_effective_approved_providers(db_session)
    assert unique_provider not in effective_approved


def test_risk_engine_integration_with_database_policies(db_session: Session):
    """RiskEngine resolves policies dynamically against PostgreSQL and alters risk scores."""
    unique_provider = f"DynamicRisk-{uuid.uuid4().hex[:6]}"
    # Seed an unapproved policy in database
    pol_unapproved = AIGovernancePolicyModel(
        external_id=f"POL-{uuid.uuid4().hex[:8].upper()}",
        provider_name=unique_provider,
        domain_signatures=["api.dynamicrisk.ai"],
        approval_status="unapproved",
        is_enabled=True,
        policy_rule="POLICY-AI-01: Prohibited Shadow AI Provider",
    )
    db_session.add(pol_unapproved)
    db_session.flush()

    # RiskEngine initialized with DB session
    engine = RiskEngine(db=db_session)
    agg = EndpointTrafficAggregate(
        target="api.dynamicrisk.ai",
        provider=unique_provider,
        category="Generative AI",
        total_calls=1,
        bytes_sent=1000,
        bytes_received=2000,
    )

    inv_item, finding = engine.evaluate_endpoint(agg)
    assert inv_item.is_approved is False
    assert inv_item.risk_score >= 50  # Baseline unapproved violation
    assert finding is not None
    assert finding.policy_rule == "POLICY-AI-01: Prohibited Shadow AI Provider"

    # Now change policy in DB to approved
    pol_unapproved.approval_status = "approved"
    pol_unapproved.policy_rule = "POLICY-AI-00: Approved Enterprise Provider"
    db_session.flush()

    # Re-evaluate with updated policy
    inv_item_updated, finding_updated = engine.evaluate_endpoint(agg)
    assert inv_item_updated.is_approved is True
    # When approved and minimal traffic (1 call, 1000 bytes sent), score is < 30
    assert inv_item_updated.risk_score < 30
    assert finding_updated is None
