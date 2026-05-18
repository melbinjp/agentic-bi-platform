"""
API Authentication Middleware

Implements simple API key-based authentication for the platform.
Assignment requirement: Section G - Security & Reliability (Data isolation, API rate limiting)
"""

import hashlib
import structlog
from datetime import datetime, timezone
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_async_session
from app.models import APIKey

logger = structlog.get_logger()

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def _has_api_keys_in_db(db: AsyncSession) -> bool:
    """Check if any API keys exist in the database."""
    result = await db.execute(select(APIKey).where(APIKey.is_active == 1).limit(1))
    return result.scalar_one_or_none() is not None


async def verify_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_async_session)
) -> str:
    """
    Verify API key from request header.
    
    Returns the API key if valid, raises HTTPException if invalid or missing.
    
    Checks database first for stored API keys, then falls back to environment variable.
    
    For demo/development:
    - If API_KEYS is empty or not configured AND no keys in database, allows all requests (open mode)
    - If API_KEYS is configured OR keys exist in database, requires valid key
    
    For production:
    - Always require API keys
    - Store keys in database for scalability and audit trail
    - Implement key rotation via API endpoints
    """
    # Development mode: if no keys configured anywhere, allow all requests
    has_db_keys = await _has_api_keys_in_db(db)
    if not settings.api_keys and not has_db_keys:
        logger.debug("api_auth_disabled", reason="no_keys_configured")
        return "development-mode"
    
    # Check if API key provided
    if not api_key:
        logger.warning("api_auth_missing", reason="no_key_in_header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check database first
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == 1
        )
    )
    api_key_record = result.scalar_one_or_none()
    
    if api_key_record:
        # Update last_used_at
        api_key_record.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        logger.debug("api_auth_success_db", key_name=api_key_record.name)
        return api_key
    
    # Fall back to environment variable
    if api_key in settings.api_keys:
        logger.debug("api_auth_success_env", key_prefix=api_key[:8])
        return api_key
    
    logger.warning("api_auth_invalid", key_prefix=api_key[:8])
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid API key",
    )


async def get_current_user(
    api_key: str = Security(verify_api_key),
    db: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Get current user information from API key.
    
    In a production system, this would:
    - Look up user ID from API key in database
    - Return user profile, permissions, quotas
    - Enable multi-tenant data isolation
    
    For this assignment:
    - Returns basic user info based on API key
    - Enables per-user rate limiting
    """
    # Check if this is a database-backed key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == 1
        )
    )
    api_key_record = result.scalar_one_or_none()
    
    if api_key_record:
        return {
            "user_id": api_key_record.name,
            "api_key": api_key,
            "permissions": ["read", "write"],
            "source": "database"
        }
    
    # Fall back to environment variable key
    return {
        "user_id": api_key[:16],  # Use key prefix as user ID
        "api_key": api_key,
        "permissions": ["read", "write"],
        "source": "environment"
    }


# Optional: API key scopes for fine-grained permissions
class APIKeyScopes:
    """Define permission scopes for API keys."""
    READ_JOBS = "jobs:read"
    WRITE_JOBS = "jobs:write"
    CANCEL_JOBS = "jobs:cancel"
    ADMIN = "admin"
    
    @classmethod
    def all_scopes(cls) -> list[str]:
        return [cls.READ_JOBS, cls.WRITE_JOBS, cls.CANCEL_JOBS, cls.ADMIN]
