from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class NoteCreate(BaseModel):
    """Schema for note creation request."""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "My First Note",
                "content": "This is the content of my note.",
            }
        }
    )


class NoteUpdate(BaseModel):
    """Schema for note update request."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Updated Title",
                "content": "Updated content.",
            }
        }
    )


class NoteOut(BaseModel):
    """Schema for note response."""

    id: PyObjectId = Field(alias="_id")
    user_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "60d5ec49f1c0d23b9a5f9e3a",
                "user_id": 1,
                "title": "My First Note",
                "content": "This is the content of my note.",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }
        },
    )
