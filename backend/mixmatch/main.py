"""Aplicația FastAPI. Toate rutele stau sub prefixul /api.

Pe server, aceeași aplicație servește și interfața compilată (vezi `mount_frontend`).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException

from mixmatch.analysis.runner import start_analysis_if_needed
from mixmatch.api import (
    collections,
    exports,
    health,
    jobs,
    library,
    mixes,
    tracks,
    transitions,
)
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
for module in (health, library, jobs, tracks, collections, mixes, transitions, exports):
    app.include_router(module.router, prefix="/api")


def mount_frontend(target: FastAPI, dist: Path) -> None:
    """Servește interfața din `dist`, dacă a fost compilată. Se înregistrează după rutele API.

    Un fișier existent se trimite ca atare; orice altă cale (rutele din browser) primește
    `index.html`. Sub `/api` nu se întoarce niciodată interfața: o rută necunoscută rămâne 404.
    """
    root = dist.resolve()
    index = root / "index.html"
    if not index.is_file():
        return

    @target.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        file = (root / path).resolve()
        if path and file.is_file() and file.is_relative_to(root):
            return FileResponse(file)
        return FileResponse(index, headers={"Cache-Control": "no-cache"})


mount_frontend(app, settings.frontend_dir)
