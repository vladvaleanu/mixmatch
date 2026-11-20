from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from mixmatch.api.deps import SessionDep
from mixmatch.db.models import Track
from mixmatch.music.camelot import classic_name

router = APIRouter(tags=["tracks"])


class TrackOut(BaseModel):
    id: int
    title: str
    artist: str | None
    duration_s: float
    bpm: float | None
    key_camelot: str | None
    key_name: str | None  # „La minor”, doar pentru afișare
    analyzed: bool  # false cât timp piesa așteaptă analiza

    @classmethod
    def from_track(cls, track: Track) -> "TrackOut":
        return cls(
            id=track.id,
            title=track.title,
            artist=track.artist,
            duration_s=track.duration_s,
            bpm=track.bpm,
            key_camelot=track.key_camelot,
            key_name=classic_name(track.key_camelot) if track.key_camelot else None,
            analyzed=track.analyzed_at is not None,
        )


@router.get("/tracks", operation_id="list_tracks")
def list_tracks(session: SessionDep) -> list[TrackOut]:
    tracks = session.scalars(select(Track).order_by(func.lower(Track.title), Track.id))
    return [TrackOut.from_track(t) for t in tracks]
