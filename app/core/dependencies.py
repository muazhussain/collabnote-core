from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.redis import get_redis
from app.db.session import get_db

bearer = HTTPBearer()


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    """Resolve and return the authenticated user from a Bearer token.

    Args:
        creds: HTTP Bearer credentials extracted from Authorization header.
        db: Async database session.
        redis: Async Redis client.

    Returns:
        Authenticated User ORM instance.

    Raises:
        HTTPException: 401 if token is invalid, revoked, or user is inactive/not found.
    """
    payload = decode_access_token(creds.credentials)
    if not payload:
        raise HTTPException(
            detail="Invalid token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not user_id or not jti:
        raise HTTPException(
            detail="Invalid token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if await redis.get(f"deny:{jti}"):
        raise HTTPException(
            detail="Token has been revoked.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            detail="User not found or inactive.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return user
