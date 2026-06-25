from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.db.models.user import User

bearer = HTTPBearer()


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve and return the authenticated user from a Bearer token.

    Args:
        creds: HTTP Bearer credentials extracted from Authorization header.
        db: Async database session.

    Returns:
        Authenticated User ORM instance.

    Raises:
        HTTPException: 401 if token is invalid or user is inactive/not found.
    """
    email = decode_access_token(creds.credentials)
    if not email:
        raise HTTPException(
            detail="Invalid token.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            detail="User not found or inactive.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return user
