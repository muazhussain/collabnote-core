from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash password using Argon2id.

    Args:
        password: Plain text password.

    Returns:
        Argon2id password hash.
    """
    return _ph.hash(password=password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against Argon2id hash.

    Args:
        plain_password: Plain text password.
        hashed_password: Stored Argon2id hash.

    Returns:
        True if password matches. Otherwise false.
    """
    try:
        return _ph.verify(hash=hashed_password, password=plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(data: dict, expire_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload to encode in the token.
        expire_delta: Custom expiry duration. Defaults to settings value.

    Returns:
        Signed JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expire_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[str]:
    """Decode and validate JWT access token.

    Args:
        token: JWT string to decode.

    Returns:
        Subject (email) from token payload, or None if invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email: Optional[str] = payload.get("sub")
        return email
    except jwt.PyJWTError:
        return None
