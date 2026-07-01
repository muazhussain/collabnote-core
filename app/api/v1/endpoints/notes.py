from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.mongo import get_mongo_db
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])

NOTES = "notes"


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> NoteOut:
    """Create a new note for the authenticated user.

    Args:
        payload: Note creation data.
        current_user: Authenticated user.
        db: Async MongoDB database.

    Returns:
        Created note.
    """
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": current_user.id,
        "title": payload.title,
        "content": payload.content,
        "created_at": now,
        "updated_at": now,
    }
    result = await db[NOTES].insert_one(doc)
    doc["_id"] = result.inserted_id
    return NoteOut.model_validate(doc)


@router.get("", response_model=list[NoteOut])
async def list_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> list[NoteOut]:
    """List all notes for the authenticated user.

    Args:
        current_user: Authenticated user.
        db: Async MongoDB database.

    Returns:
        List of notes ordered by newest first.
    """
    cursor = db[NOTES].find({"user_id": current_user.id}).sort("created_at", -1)
    docs = await cursor.to_list(length=None)
    return [NoteOut.model_validate(doc) for doc in docs]


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> NoteOut:
    """Retrieve a single note by ID.

    Args:
        note_id: MongoDB ObjectId of the note.
        current_user: Authenticated user.
        db: Async MongoDB database.

    Returns:
        Note document.

    Raises:
        HTTPException: 404 if note not found or not owned by current user.
    """
    if not ObjectId.is_valid(note_id):
        raise HTTPException(
            detail="Invalid note ID.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    doc = await db[NOTES].find_one(
        {"_id": ObjectId(note_id), "user_id": current_user.id}
    )
    if not doc:
        raise HTTPException(
            detail="Note not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return NoteOut.model_validate(doc)


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: str,
    payload: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> NoteOut:
    """Update a note by ID.

    Args:
        note_id: MongoDB ObjectId of the note.
        payload: Fields to update.
        current_user: Authenticated user.
        db: Async MongoDB database.

    Returns:
        Updated note.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if note not found or not owned by current user.
    """
    if not ObjectId.is_valid(note_id):
        raise HTTPException(
            detail="Invalid note ID.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            detail="No fields to update.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    updates["updated_at"] = datetime.now(timezone.utc)
    result = await db[NOTES].find_one_and_update(
        {"_id": ObjectId(note_id), "user_id": current_user.id},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(
            detail="Note not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return NoteOut.model_validate(result)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> None:
    """Delete a note by ID.

    Args:
        note_id: MongoDB ObjectId of the note.
        current_user: Authenticated user.
        db: Async MongoDB database.

    Raises:
        HTTPException: 404 if note not found or not owned by current user.
    """
    if not ObjectId.is_valid(note_id):
        raise HTTPException(
            detail="Invalid note ID.", status_code=status.HTTP_404_NOT_FOUND
        )
    result = await db[NOTES].delete_one(
        {"_id": ObjectId(note_id), "user_id": current_user.id}
    )
    if result.deleted_count == 0:
        raise HTTPException(
            detail="Note not found.", status_code=status.HTTP_404_NOT_FOUND
        )
