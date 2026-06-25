from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user.

    Args:
        current_user: Authenticated user resolved from Bearer token.

    Returns:
        Current user data.
    """
    return current_user
