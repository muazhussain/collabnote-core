from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration request."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, description="Minimum 6 characters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "alice@example.com",
                "username": "alice",
                "password": "securepassword123",
            }
        }
    )


class UserOut(BaseModel):
    """Schema for user response."""

    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "alice@example.com",
                "username": "alice",
                "is_active": True,
                "created_at": "2026-01-01T00:00:00",
            }
        },
    )
