import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AdminUser:
    """Represents an authenticated administrator performing policy operations."""
    username: str = "admin"
    role: str = "admin"


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    if salt is None:
        salt = os.urandom(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Securely verifies a plaintext password against a stored PBKDF2 hash using constant-time comparison."""
    if not hashed_password or not plain_password:
        return False
    try:
        parts = hashed_password.strip().split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
        computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(computed, expected)
    except Exception as exc:
        logger.warning("Failed password verification attempt: %s", type(exc).__name__)
        return False


def _b64encode_str(data: bytes) -> str:
    """Encodes bytes to URL-safe base64 string without trailing padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode_str(s: str) -> bytes:
    """Decodes URL-safe base64 string with restored padding."""
    padding = len(s) % 4
    if padding > 0:
        s += "=" * (4 - padding)
    return base64.urlsafe_b64decode(s.encode("utf-8"))


def create_access_token(data: Dict[str, Any], expires_minutes: int = 480) -> str:
    """Generates an HMAC-SHA256 signed bearer access token with expiration timestamp.
    
    Structure: <payload_b64>.<sig_b64>
    """
    secret = getattr(settings, "SECRET_KEY", "shadow-ai-jwt-signing-secret-key-change-in-production")
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)

    payload = dict(data)
    payload["iat"] = int(now.timestamp())
    payload["exp"] = int(exp.timestamp())

    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64encode_str(payload_json)

    signature = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = _b64encode_str(signature)

    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates the signature and expiration timestamp of an HMAC-SHA256 token.
    
    Raises HTTPException(401) on invalid signature or expiration.
    """
    secret = getattr(settings, "SECRET_KEY", "shadow-ai-jwt-signing-secret-key-change-in-production")
    parts = token.strip().split(".")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token structure.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload_b64, sig_b64 = parts[0], parts[1]

    try:
        expected_sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
        actual_sig = _b64decode_str(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token signature.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload_bytes = _b64decode_str(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Token decoding failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    exp = payload.get("exp")
    if exp is not None:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if now_ts > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return payload


def get_current_admin(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> AdminUser:
    """Dependency that verifies administrative credentials and role authorization.
    
    Returns 401 if credentials are missing, expired, or invalid.
    Returns 403 if authenticated caller lacks administrative privileges.
    """
    token = None
    if x_admin_token:
        token = x_admin_token.strip()
    elif authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]

    if not token:
        logger.warning("Unauthorized access attempt: Missing administrative authorization credentials.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator authorization required. Provide valid token via 'X-Admin-Token' or 'Authorization: Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expected_api_key = getattr(settings, "ADMIN_API_KEY", "shadow-ai-admin-secret-key")

    # 1. Check for administrative API key match (backward compatibility & service keys)
    if hmac.compare_digest(token, expected_api_key):
        return AdminUser(username=getattr(settings, "ADMIN_USERNAME", "admin"), role="admin")

    # 2. Check for signed bearer token
    try:
        payload = decode_access_token(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials or token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = payload.get("role", "")
    username = payload.get("sub", "admin")

    if role != "admin":
        logger.warning("Forbidden access attempt: User '%s' with role '%s' attempted admin operation.", username, role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrative privileges are required to perform this action.",
        )

    return AdminUser(username=username, role="admin")


def get_optional_admin(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[AdminUser]:
    """Optional admin dependency for endpoints that accept both anonymous and admin callers."""
    try:
        return get_current_admin(x_admin_token=x_admin_token, authorization=authorization)
    except HTTPException:
        return None
