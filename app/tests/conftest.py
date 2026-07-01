from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.main import app

_engine = create_async_engine(settings.database_url)
_TestSession = async_sessionmaker(_engine, expire_on_commit=False)

_TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword123",
}


@pytest.fixture(scope="session", autouse=True)
async def create_tables() -> AsyncGenerator[None, None]:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest.fixture(autouse=True)
async def clean_db() -> AsyncGenerator[None, None]:
    yield
    async with _TestSession() as session:
        await session.execute(text("TRUNCATE TABLE users CASCADE"))
        await session.commit()


@pytest.fixture(autouse=True)
async def clean_redis() -> AsyncGenerator[None, None]:
    yield
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis.flushdb()
    await redis.aclose()


@pytest.fixture(autouse=True)
async def clean_mongo() -> AsyncGenerator[None, None]:
    yield
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_url)
    await client[settings.mongodb_db_name]["notes"].drop()
    client.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/register", json=_TEST_USER)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": _TEST_USER["username"], "password": _TEST_USER["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
