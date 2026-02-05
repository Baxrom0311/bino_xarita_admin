# app/api/auth.py
"""
Authentication endpoints for login and token management
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from datetime import timedelta
from app.core.security import create_access_token, decode_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.core.login_security import login_security
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


def get_admin_user():
    """Load admin user from app settings"""
    username = settings.ADMIN_USERNAME
    password_hash = settings.ADMIN_PASSWORD_HASH
    
    if not password_hash:
        if settings.is_production:
            logger.error("ADMIN_PASSWORD_HASH is not set; admin JWT login is disabled in production.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin login is not configured",
            )

        if not settings.DEBUG:
            logger.error("ADMIN_PASSWORD_HASH is not set; admin JWT login is disabled (set DEBUG=true to allow insecure fallback).")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin login is not configured",
            )

        # Development-only fallback (insecure): keep the app usable locally.
        logger.warning(
            "⚠️  ADMIN_PASSWORD_HASH not set in .env! Using insecure default password for development. "
            "Run 'python scripts/create_admin.py' to create secure credentials."
        )
        password_hash = get_password_hash("admin123456")
    
    return {
        "username": username,
        "hashed_password": password_hash,
        "role": "admin"
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, request: Request):
    """
    Login endpoint to get JWT access token
    
    **Note:** This is a temporary implementation. In production:
    - Use database for user management
    - Implement proper user registration
    - Add account lockout after failed attempts
    - Add 2FA support
    """
    # Basic protections against brute-force / accidental abuse
    login_security.check_rate_limit(request)
    login_security.check_lockout(request, credentials.username)

    user = get_admin_user()
    
    if credentials.username != user["username"] or not verify_password(credentials.password, user["hashed_password"]):
        login_security.register_failure(request, credentials.username)
        logger.warning(
            "admin_login_failed username=%s ip=%s user_agent=%s",
            credentials.username,
            request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown"),
            request.headers.get("user-agent", "-"),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    login_security.register_success(request, credentials.username)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    logger.info(
        "admin_login_success username=%s ip=%s user_agent=%s",
        credentials.username,
        request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown"),
        request.headers.get("user-agent", "-"),
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Refresh the current access token.

    Notes:
    - This is not a full refresh-token (rotating) implementation.
    - It only refreshes a still-valid token.
    """
    token = credentials.credentials

    # Transition helper: if legacy admin token is used, issue a JWT.
    if secrets.compare_digest(token, settings.ADMIN_TOKEN):
        user = get_admin_user()
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]},
            expires_delta=access_token_expires,
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    payload = decode_access_token(token)
    if payload.get("role") != "admin" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": payload["sub"], "role": payload.get("role", "admin")},
        expires_delta=access_token_expires,
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
