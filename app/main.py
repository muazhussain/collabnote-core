from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title=settings.app_name,
    description="Collabnote Core",
    version=settings.version,
    lifespan=lifespan,
)

app.include_router(v1_router)


@app.get("/ping")
async def ping() -> dict[str, str]:
    return {"status": "ok"}
