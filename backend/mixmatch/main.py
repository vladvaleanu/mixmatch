"""Aplicația FastAPI. Toate rutele stau sub prefixul /api."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mixmatch.analysis.runner import start_analysis_if_needed
from mixmatch.api import health, jobs, library, mixes, tracks
from mixmatch.api.errors import install_error_handlers
from mixmatch.config import settings
from mixmatch.db.session import SessionLocal, run_migrations
from mixmatch.jobs import queue


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    run_migrations(settings.db_url)
    queue.fail_interrupted()
    start_analysis_if_needed(queue, SessionLocal)  # piese rămase neanalizate sau versiune nouă
    yield
    queue.shutdown()


app = FastAPI(title="mixmatch", version=settings.version, lifespan=lifespan)
install_error_handlers(app)
for module in (health, library, jobs, tracks, mixes):
    app.include_router(module.router, prefix="/api")
