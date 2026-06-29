from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    """Return the shared async Redis client."""
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


RedisDep = Annotated[Redis, Depends(get_redis)]
