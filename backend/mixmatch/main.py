"""Aplicația FastAPI. Toate rutele stau sub prefixul /api."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mixmatch.api import health
from mixmatch.config import settings
from mixmatch.db.session import run_migrations
from mixmatch.jobs import queue


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    run_migrations(settings.db_url)
    queue.fail_interrupted()
    yield
    queue.shutdown()


app = FastAPI(title="mixmatch", version=settings.version, lifespan=lifespan)
app.include_router(health.router, prefix="/api")
