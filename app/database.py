from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all sqlalchemy models."""

    pass


engine = create_async_engine(
    url=settings.database_url,
    echo=False,
)

async_session = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session.
    """
    async with async_session() as session:
        yield session
