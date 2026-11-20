from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.db.models import Track, Waveform
from mixmatch.music.camelot import classic_name

router = APIRouter(tags=["tracks"])

EnergyLevel = Annotated[int, Field(ge=1, le=5)]


class TrackOut(BaseModel):
    id: int
    title: str
    artist: str | None
    duration_s: float
    bpm: float | None
    key_camelot: str | None
    key_name: str | None  # „La minor”, doar pentru afișare
    energy: int | None  # efectivă: corectura manuală, dacă există, altfel cea automată
    energy_manual: int | None
    intro_bars: int | None
    outro_bars: int | None
    waveform_preview: list[int] | None  # 40 de vârfuri 0–255, pentru rândul din tabel
    analyzed: bool  # false cât timp piesa așteaptă analiza

    @classmethod
    def from_track(cls, track: Track, preview: bytes | None) -> "TrackOut":
        return cls(
            id=track.id,
            title=track.title,
            artist=track.artist,
            duration_s=track.duration_s,
            bpm=track.bpm,
            key_camelot=track.key_camelot,
            key_name=classic_name(track.key_camelot) if track.key_camelot else None,
            energy=track.energy_effective,
            energy_manual=track.energy_manual,
            intro_bars=track.intro_bars,
            outro_bars=track.outro_bars,
            waveform_preview=list(preview) if preview else None,
            analyzed=track.analyzed_at is not None,
        )


class TrackPatch(BaseModel):
    energy_manual: EnergyLevel | None  # null = revino la energia automată


@router.get("/tracks", operation_id="list_tracks")
def list_tracks(session: SessionDep) -> list[TrackOut]:
    rows = session.execute(
        select(Track, Waveform.preview)
        .outerjoin(Waveform, Waveform.track_id == Track.id)
        .order_by(func.lower(Track.title), Track.id)
    )
    return [TrackOut.from_track(track, preview) for track, preview in rows]


@router.patch("/tracks/{track_id}", operation_id="update_track", responses=responses(404))
def update_track(track_id: int, body: TrackPatch, session: SessionDep) -> TrackOut:
    """Corecturi manuale. Deocamdată: energia (`energy_manual`)."""
    track = session.get(Track, track_id)
    if track is None:
        raise ApiError(404, "track_not_found", f"Piesa {track_id} nu există")
    track.energy_manual = body.energy_manual
    session.commit()
    preview = session.scalar(select(Waveform.preview).where(Waveform.track_id == track_id))
    return TrackOut.from_track(track, preview)
