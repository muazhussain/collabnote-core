from collections.abc import AsyncGenerator, Generator

import psycopg
import pymongo
import pytest
import redis as sync_redis_lib
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.db.mongo as _mongo_module
import app.db.redis as _redis_module
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
def clean_db() -> Generator[None, None, None]:
    yield
    url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as conn:
        conn.execute("TRUNCATE TABLE users CASCADE")
        conn.commit()


@pytest.fixture(autouse=True)
def clean_redis() -> Generator[None, None, None]:
    yield
    r = sync_redis_lib.from_url(str(settings.redis_url))
    r.flushdb()
    r.close()
    _redis_module._redis = None


@pytest.fixture(autouse=True)
def clean_mongo() -> Generator[None, None, None]:
    yield
    client: pymongo.MongoClient = pymongo.MongoClient(settings.mongodb_url)
    client[settings.mongodb_db_name]["notes"].drop()
    client.close()
    _mongo_module._client = None


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
    token = str(resp.json()["access_token"])
    return {"Authorization": f"Bearer {token}"}
