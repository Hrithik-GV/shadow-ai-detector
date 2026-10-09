from dataclasses import dataclass
import hmac
import logging
from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AdminUser:
    """Represents an authenticated administrator performing policy operations."""
    username: str = "admin"
    role: str = "admin"


def get_current_admin(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> AdminUser:
    """Dependency that verifies administrative credentials for protected operations."""
    token = None
    if x_admin_token:
        token = x_admin_token.strip()
    elif authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]

    expected_key = getattr(settings, "ADMIN_API_KEY", "shadow-ai-admin-secret-key")

    if not token or not hmac.compare_digest(token, expected_key):
        logger.warning("Unauthorized attempt to access administrative policy endpoint.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator authorization required. Provide valid token via 'X-Admin-Token' or 'Authorization: Bearer <key>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AdminUser(username="admin", role="admin")


def get_optional_admin(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[AdminUser]:
    """Optional admin dependency for endpoints that accept both anonymous and admin callers."""
    try:
        return get_current_admin(x_admin_token=x_admin_token, authorization=authorization)
    except HTTPException:
        return None
