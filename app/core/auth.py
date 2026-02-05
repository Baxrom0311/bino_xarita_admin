# app/core/auth.py
"""
Admin authentication helpers.

Supports:
- Legacy static admin token (`ADMIN_TOKEN`)
- Admin JWT tokens issued by `/api/auth/login`
"""
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.security import decode_access_token

security_required = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def _is_legacy_admin_token(token: str) -> bool:
    return secrets.compare_digest(token, settings.ADMIN_TOKEN)


def _is_admin_jwt(token: str) -> bool:
    # Quick shape check to avoid noisy JWT decode attempts for obviously-non-JWT tokens.
    if token.count(".") != 2:
        return False
    try:
        payload = decode_access_token(token)
    except HTTPException:
        return False
    return payload.get("role") == "admin" and bool(payload.get("sub"))

async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_required)
) -> str:
    """
    Verify admin token from Authorization header.
    
    Usage:
        @router.delete("/{id}")
        async def delete_item(id: int, token: str = Depends(verify_admin_token)):
            ...
    """
    token = credentials.credentials

    # 1) Legacy token (backwards-compatible with existing frontend)
    if _is_legacy_admin_token(token):
        return token

    # 2) Admin JWT (newer flow via /api/auth/login)
    if _is_admin_jwt(token):
        return token

    # Invalid credentials (keep the same response semantics as before)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Optional: make some endpoints public, others protected
def optional_admin_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional)
) -> bool:
    """Returns True if valid admin credentials are present, False otherwise."""
    if not credentials:
        return False
    token = credentials.credentials
    return _is_legacy_admin_token(token) or _is_admin_jwt(token)
