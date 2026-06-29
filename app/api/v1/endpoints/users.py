from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserOut)
async def get_profile(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user's profile."""
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> User:
    """Get a user by ID.

    Raises:
        HTTPException: 404 if user not found.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    return user


@router.patch("/profile", response_model=UserOut)
async def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update the currently authenticated user's profile.

    Raises:
        HTTPException: 409 if email or username already taken.
    """
    if payload.email and payload.email != current_user.email:
        exists = await db.execute(select(User).where(User.email == payload.email))
        if exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already taken."
            )
        current_user.email = payload.email

    if payload.username and payload.username != current_user.username:
        exists = await db.execute(select(User).where(User.username == payload.username))
        if exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already taken."
            )
        current_user.username = payload.username

    if payload.password:
        current_user.password_hash = hash_password(payload.password)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete the currently authenticated user's account."""
    await db.delete(current_user)
    await db.commit()
