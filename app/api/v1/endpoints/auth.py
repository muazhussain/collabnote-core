from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import bearer, get_current_user
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User
from app.db.redis import get_redis
from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """Register a new user account.

    Raises:
        HTTPException: 409 if email or username already exists.
    """
    result = await db.execute(
        select(User).where(
            (User.email == payload.email) | (User.username == payload.username)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered.",
        )
    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate via OAuth2 password flow and return a JWT access token.

    Raises:
        HTTPException: 401 if credentials are invalid or account is inactive.
    """
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if (
        not user
        or not user.is_active
        or not verify_password(form.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )
    return Token(access_token=create_access_token(data={"sub": str(user.id)}))


@router.post("/refresh", response_model=Token)
async def refresh(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> Token:
    """Issue a new access token and revoke the current one."""
    payload = decode_access_token(creds.credentials)
    assert payload is not None
    old_jti = payload["jti"]
    ttl = int(payload["exp"] - datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        await redis.set(f"deny:{old_jti}", "1", ex=ttl)
    return Token(access_token=create_access_token(data={"sub": str(current_user.id)}))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    _: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> None:
    """Blacklist the current access token."""
    payload = decode_access_token(creds.credentials)
    assert payload is not None
    jti = payload["jti"]
    ttl = int(payload["exp"] - datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        await redis.set(f"deny:{jti}", "1", ex=ttl)
