from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select

from mixmatch.api.deps import SessionDep
from mixmatch.db.models import Track

router = APIRouter(tags=["tracks"])


class TrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    artist: str | None
    duration_s: float


@router.get("/tracks", operation_id="list_tracks")
def list_tracks(session: SessionDep) -> list[TrackOut]:
    tracks = session.scalars(select(Track).order_by(func.lower(Track.title), Track.id))
    return [TrackOut.model_validate(t) for t in tracks]
