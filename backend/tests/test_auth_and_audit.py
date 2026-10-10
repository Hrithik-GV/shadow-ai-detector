import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import (
    AdminUser,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.models.governance import AIGovernancePolicyModel, PolicyAuditLogModel
from app.services.policy_service import PolicyService


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


# ==============================================================================
# 1. Cryptographic Password Hashing & Verification Tests
# ==============================================================================

def test_password_hashing_and_verification():
    """Verify that PBKDF2 password hashing produces valid hashes and verifies securely."""
    password = "SuperSecretAdminPassword2026!"
    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2_sha256$100000$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "") is False
    assert verify_password(password, "malformed_hash") is False


def test_password_hash_salt_uniqueness():
    """Verify that hashing the same password twice produces distinct hashes due to random salts."""
    pwd = "IdenticalPassword"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)
    assert hash1 != hash2
    assert verify_password(pwd, hash1) is True
    assert verify_password(pwd, hash2) is True


# ==============================================================================
# 2. Token Creation, Validation & Expiration Tests
# ==============================================================================

def test_access_token_creation_and_decoding():
    """Verify signed access token roundtrip."""
    payload_data = {"sub": "admin_user", "role": "admin"}
    token = create_access_token(payload_data, expires_minutes=60)

    decoded = decode_access_token(token)
    assert decoded["sub"] == "admin_user"
    assert decoded["role"] == "admin"
    assert "exp" in decoded
    assert "iat" in decoded


def test_access_token_signature_tampering_rejected():
    """Verify that tampered tokens fail signature verification with 401."""
    token = create_access_token({"sub": "admin", "role": "admin"})
    parts = token.split(".")
    tampered = f"{parts[0]}.bad_signature"

    with pytest.raises(Exception) as excinfo:
        decode_access_token(tampered)
    assert "401" in str(excinfo.value) or excinfo.value.status_code == 401


def test_access_token_expired_rejected():
    """Verify that expired tokens fail validation with 401."""
    # Negative expiration minutes to simulate expired token
    token = create_access_token({"sub": "admin", "role": "admin"}, expires_minutes=-10)

    with pytest.raises(Exception) as excinfo:
        decode_access_token(token)
    assert "401" in str(excinfo.value) or excinfo.value.status_code == 401


# ==============================================================================
# 3. Authentication Endpoint (/api/auth/login and /api/auth/me) Tests
# ==============================================================================

def test_login_success_with_default_credentials(client: TestClient):
    """Admin can authenticate via POST /api/auth/login and receive signed bearer token."""
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["username"] == "admin"
    assert data["expires_in"] > 0

    token = data["access_token"]
    # Verify token can access /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "admin"
    assert me_data["role"] == "admin"


def test_login_success_versioned_alias(client: TestClient):
    """POST /api/v1/auth/login behaves identically to /api/auth/login."""
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials_returns_401(client: TestClient):
    """Invalid credentials return 401 without exposing stack traces or internals."""
    res_wrong_pw = client.post("/api/auth/login", json={"username": "admin", "password": "incorrect_password"})
    assert res_wrong_pw.status_code == 401
    assert "detail" in res_wrong_pw.json()
    assert "traceback" not in res_wrong_pw.text.lower()

    res_wrong_user = client.post("/api/auth/login", json={"username": "nonexistent", "password": "admin123"})
    assert res_wrong_user.status_code == 401


# ==============================================================================
# 4. Role-Based Authorization Tests (401 vs 403)
# ==============================================================================

def test_policy_mutations_require_authentication_401(client: TestClient):
    """Missing or invalid token returns 401 Unauthorized."""
    payload = {
        "provider_name": "TestAI",
        "domain_signatures": ["api.testai.corp"],
        "approval_status": "approved",
    }
    # Missing token
    res_no_token = client.post("/api/policies", json=payload)
    assert res_no_token.status_code == 401
    assert "WWW-Authenticate" in res_no_token.headers

    # Invalid token
    res_bad_token = client.post(
        "/api/policies",
        json=payload,
        headers={"Authorization": "Bearer invalid_token_xyz"},
    )
    assert res_bad_token.status_code == 401


def test_policy_mutations_reject_non_admin_role_403(client: TestClient):
    """A valid token with a non-admin role (e.g., 'viewer') is rejected with 403 Forbidden."""
    viewer_token = create_access_token({"sub": "viewer_user", "role": "viewer"})
    headers = {"Authorization": f"Bearer {viewer_token}"}

    payload = {
        "provider_name": "ViewerAttemptAI",
        "domain_signatures": ["api.viewerai.corp"],
        "approval_status": "approved",
    }
    response = client.post("/api/policies", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Administrative privileges are required" in response.json()["detail"]


def test_audit_logs_reject_non_admin_role_403(client: TestClient):
    """Non-admin user cannot access policy audit logs."""
    viewer_token = create_access_token({"sub": "viewer_user", "role": "viewer"})
    headers = {"Authorization": f"Bearer {viewer_token}"}

    response = client.get("/api/policies/audit-logs", headers=headers)
    assert response.status_code == 403


# ==============================================================================
# 5. Audit Logging Protection, Outcome & Pagination Tests
# ==============================================================================

def test_audit_logs_endpoint_requires_admin_auth(client: TestClient):
    """GET /api/policies/audit-logs is protected and requires admin credentials."""
    # Anonymous request
    res_anon = client.get("/api/policies/audit-logs")
    assert res_anon.status_code == 401

    # Admin request
    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    res_admin = client.get("/api/policies/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert isinstance(res_admin.json(), list)


def test_audit_trail_recorded_for_all_mutations(client: TestClient, db_session: Session):
    """Verify that creating, updating status, disabling, and deleting a policy records audit entries with outcome."""
    admin_token = create_access_token({"sub": "sec_admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}
    provider_name = f"AuditTrailAI-{uuid.uuid4().hex[:6]}"

    # 1. Create policy
    create_res = client.post(
        "/api/policies",
        json={
            "provider_name": provider_name,
            "domain_signatures": ["api.auditai.test"],
            "approval_status": "approved",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    policy_id = create_res.json()["id"]

    # 2. Update status
    status_res = client.patch(
        f"/api/policies/{policy_id}/status",
        json={"approval_status": "blocked", "notes": "Blocked due to policy audit test"},
        headers=headers,
    )
    assert status_res.status_code == 200

    # 3. Disable policy
    disable_res = client.post(f"/api/policies/{policy_id}/disable", headers=headers)
    assert disable_res.status_code == 200

    # 4. Fetch audit logs and verify actor, actions, outcome
    audit_res = client.get("/api/policies/audit-logs", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()

    provider_logs = [l for l in logs if l.get("providerName") == provider_name or l.get("provider_name") == provider_name]
    assert len(provider_logs) >= 3

    actions = {l["action"] for l in provider_logs}
    assert "create" in actions
    assert "status_change" in actions
    assert "disable" in actions

    for log in provider_logs:
        assert log["performedBy"] == "sec_admin" or log["performed_by"] == "sec_admin"
        assert log.get("outcome") == "SUCCESS"
        assert "password" not in str(log).lower()
        assert "token" not in str(log).lower()


def test_audit_logs_pagination(client: TestClient):
    """Verify skip and limit pagination parameters on GET /api/policies/audit-logs."""
    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    res_all = client.get("/api/policies/audit-logs?limit=50", headers=headers)
    assert res_all.status_code == 200
    all_logs = res_all.json()

    if len(all_logs) > 1:
        res_limit_1 = client.get("/api/policies/audit-logs?limit=1", headers=headers)
        assert res_limit_1.status_code == 200
        assert len(res_limit_1.json()) == 1
        assert res_limit_1.json()[0]["id"] == all_logs[0]["id"]

        res_skip_1 = client.get("/api/policies/audit-logs?skip=1&limit=1", headers=headers)
        assert res_skip_1.status_code == 200
        assert len(res_skip_1.json()) == 1
        assert res_skip_1.json()[0]["id"] == all_logs[1]["id"]
