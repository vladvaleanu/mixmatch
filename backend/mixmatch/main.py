"""Aplicația FastAPI. Toate rutele stau sub prefixul /api."""

from fastapi import FastAPI

from mixmatch.api import health
from mixmatch.config import settings

app = FastAPI(title="mixmatch", version=settings.version)
app.include_router(health.router, prefix="/api")
