import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import AdminUser, create_access_token, get_current_admin, verify_password
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    """Payload to authenticate administrative user."""
    username: str = Field(..., min_length=1, max_length=100, description="Administrator username")
    password: str = Field(..., min_length=1, description="Administrator password")


class TokenResponse(BaseModel):
    """Authentication token response payload."""
    access_token: str = Field(..., description="Signed bearer access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token validity window in seconds")
    role: str = Field("admin", description="Granted user authorization role")
    username: str = Field("admin", description="Authenticated username")


class UserProfileResponse(BaseModel):
    """Authenticated user profile representation."""
    username: str
    role: str


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate administrator credentials",
    description="Validates administrative credentials against stored PBKDF2 password hashes and returns a signed bearer access token.",
)
def login(payload: LoginRequest) -> TokenResponse:
    """Authenticates admin and returns a signed bearer token."""
    expected_username = getattr(settings, "ADMIN_USERNAME", "admin")
    stored_hash = getattr(settings, "ADMIN_PASSWORD_HASH", "")

    is_user_valid = payload.username.strip().lower() == expected_username.strip().lower()
    is_pass_valid = False

    if stored_hash:
        is_pass_valid = verify_password(payload.password, stored_hash)
    
    # Secondary check against ADMIN_API_KEY for developer/CLI setups
    if not is_pass_valid:
        expected_key = getattr(settings, "ADMIN_API_KEY", "")
        if expected_key and payload.password == expected_key:
            is_pass_valid = True

    if not is_user_valid or not is_pass_valid:
        logger.warning("Failed login attempt for user '%s'.", payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_minutes = 480  # 8 hours
    token = create_access_token(
        data={"sub": expected_username, "role": "admin"},
        expires_minutes=expires_minutes,
    )

    logger.info("Admin user '%s' authenticated successfully.", expected_username)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_minutes * 60,
        role="admin",
        username=expected_username,
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated admin profile",
    description="Returns current authenticated user details and active role.",
)
def get_current_user_profile(
    admin: AdminUser = Depends(get_current_admin),
) -> UserProfileResponse:
    """Returns profile of current authenticated administrator."""
    return UserProfileResponse(
        username=admin.username,
        role=admin.role,
    )
