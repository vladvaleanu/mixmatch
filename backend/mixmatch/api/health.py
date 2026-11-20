from fastapi import APIRouter
from pydantic import BaseModel

from mixmatch.config import settings

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: str
    version: str


@router.get("/health", operation_id="get_health")
def get_health() -> Health:
    return Health(status="ok", version=settings.version)
