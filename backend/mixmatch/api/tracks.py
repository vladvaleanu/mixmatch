from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import or_, select

from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.db.models import CollectionTrack, MixItem, Track, Waveform
from mixmatch.library.playback import MAX_CLIP_S, playable_file, render_clip
from mixmatch.music.camelot import classic_name, parse
from mixmatch.music.compat import Label, TrackInfo, match, suggestion_rank
from mixmatch.text import sort_key

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
    collection_ids: list[int] = []  # colecțiile în care e piesa

    @classmethod
    def from_track(
        cls, track: Track, preview: bytes | None, collection_ids: list[int] | None = None
    ) -> "TrackOut":
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
            collection_ids=collection_ids or [],
        )


class TrackPatch(BaseModel):
    energy_manual: EnergyLevel | None  # null = revino la energia automată


def _get_track(session: SessionDep, track_id: int) -> Track:
    track = session.get(Track, track_id)
    if track is None:
        raise ApiError(404, "track_not_found", f"Piesa {track_id} nu există")
    return track


Sort = Literal["title", "bpm", "key", "energy", "duration", "recent"]
CamelotCode = Annotated[str, Field(pattern=r"^(1[0-2]|[1-9])[AB]$")]


def _sort_key(sort: Sort):  # type: ignore[no-untyped-def]
    """Piesele fără valoare (neanalizate) ajung la final."""
    missing = float("inf")
    return {
        "title": lambda t: (sort_key(t.title), t.id),
        "bpm": lambda t: (t.bpm if t.bpm is not None else missing, t.id),
        "key": lambda t: (parse(t.key_camelot) if t.key_camelot else (99, "Z"), t.id),
        "energy": lambda t: (
            t.energy_effective if t.energy_effective is not None else missing,
            t.id,
        ),
        "duration": lambda t: (t.duration_s, t.id),
        "recent": lambda t: (-t.added_at.timestamp(), -t.id),  # cele mai noi primele
    }[sort]


@router.get("/tracks", operation_id="list_tracks", responses=responses(404))
def list_tracks(
    session: SessionDep,
    q: str | None = None,
    bpm_min: float | None = None,
    bpm_max: float | None = None,
    energy: Annotated[list[Annotated[int, Field(ge=1, le=5)]] | None, Query()] = None,
    key: Annotated[list[CamelotCode] | None, Query()] = None,
    compatible_with: int | None = None,
    collection: int | None = None,
    sort: Sort = "title",
) -> list[TrackOut]:
    """Biblioteca, cu filtre. `compatible_with`: doar piesele care merg (Lin sau Bun) după ea."""
    query = select(Track, Waveform.preview).outerjoin(Waveform, Waveform.track_id == Track.id)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Track.title.ilike(pattern), Track.artist.ilike(pattern)))
    if bpm_min is not None:
        query = query.where(Track.bpm >= bpm_min)
    if bpm_max is not None:
        query = query.where(Track.bpm <= bpm_max)
    if energy:
        query = query.where(Track.energy_effective.in_(energy))
    if key:
        query = query.where(Track.key_camelot.in_(key))
    if collection is not None:
        query = query.where(
            Track.id.in_(
                select(CollectionTrack.track_id).where(CollectionTrack.collection_id == collection)
            )
        )
    rows = [(track, preview) for track, preview in session.execute(query)]

    if compatible_with is not None:
        reference = TrackInfo.of(_get_track(session, compatible_with))
        if reference is None:
            return []
        rows = [
            (track, preview)
            for track, preview in rows
            if track.id != compatible_with
            and (info := TrackInfo.of(track)) is not None
            and match(reference, info).label != Label.caution
        ]
    rows.sort(key=lambda row: _sort_key(sort)(row[0]))
    memberships = _collections_of(session)
    return [
        TrackOut.from_track(track, preview, memberships.get(track.id)) for track, preview in rows
    ]


def _collections_of(session: SessionDep) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for track_id, collection_id in session.execute(
        select(CollectionTrack.track_id, CollectionTrack.collection_id)
    ):
        out.setdefault(track_id, []).append(collection_id)
    return out


class MatchOut(BaseModel):
    track: TrackOut
    label: Label
    score: int  # 0–100
    reason: str  # „8A → 9A · −1 BPM”


@router.get("/tracks/{track_id}/matches", operation_id="list_matches", responses=responses(404))
def list_matches(
    track_id: int,
    session: SessionDep,
    limit: Annotated[int, Field(ge=1, le=50)] = 10,
    exclude_mix: int | None = None,
    target_energy: Annotated[float | None, Field(ge=1, le=5)] = None,
) -> list[MatchOut]:
    """Piesele care merg bine după aceasta (Lin sau Bun): întâi Lin, apoi după scor.

    Același fișier aflat în mai multe foldere (același `file_hash`) apare o singură dată.
    `exclude_mix`: fără piesele deja în acel mix. `target_energy`: energia dorită de curba
    mixului pe poziția următoare; între sugestii de aceeași etichetă, cele mai apropiate de ea
    urcă în listă.
    """
    current = _get_track(session, track_id)
    reference = TrackInfo.of(current)
    if reference is None:
        return []
    query = (
        select(Track, Waveform.preview)
        .outerjoin(Waveform, Waveform.track_id == Track.id)
        .where(Track.id != track_id)
    )
    if exclude_mix is not None:
        query = query.where(
            Track.id.not_in(select(MixItem.track_id).where(MixItem.mix_id == exclude_mix))
        )
    rows = session.execute(query)
    found = []
    for track, preview in rows:
        info = TrackInfo.of(track)
        if info is None or track.file_hash == current.file_hash:
            continue
        result = match(reference, info)
        if result.label != Label.caution:
            found.append((result, track, preview))

    found.sort(
        key=lambda item: (
            *suggestion_rank(item[0], item[1].energy_effective, target_energy),
            item[1].title.casefold(),
        )
    )
    unique, seen = [], set()
    for item in found:  # după sortare, deci rămâne cea mai bună copie
        if item[1].file_hash not in seen:
            seen.add(item[1].file_hash)
            unique.append(item)
    found = unique
    return [
        MatchOut(
            track=TrackOut.from_track(track, preview),
            label=result.label,
            score=result.score,
            reason=result.reason,
        )
        for result, track, preview in found[:limit]
    ]


@router.patch("/tracks/{track_id}", operation_id="update_track", responses=responses(404))
def update_track(track_id: int, body: TrackPatch, session: SessionDep) -> TrackOut:
    """Corecturi manuale. Deocamdată: energia (`energy_manual`)."""
    track = _get_track(session, track_id)
    track.energy_manual = body.energy_manual
    session.commit()
    preview = session.scalar(select(Waveform.preview).where(Waveform.track_id == track_id))
    return TrackOut.from_track(track, preview, _collections_of(session).get(track_id))


@router.get(
    "/tracks/{track_id}/audio",
    operation_id="get_track_audio",
    response_class=FileResponse,
    responses={**responses(404), 200: {"content": {"audio/*": {}}}},
)
def get_track_audio(track_id: int, session: SessionDep) -> FileResponse:
    """Fișierul audio, cu suport pentru Range (derulare). AIFF se servește convertit în FLAC."""
    track = _get_track(session, track_id)
    try:
        path, media_type = playable_file(Path(track.path), track.file_hash)
    except FileNotFoundError as exc:
        raise ApiError(404, "file_missing", f"Fișierul nu mai există: {track.path}") from exc
    return FileResponse(path, media_type=media_type)


class WaveformOut(BaseModel):
    peaks: list[int]  # 0–255, egal distanțate pe toată durata piesei


@router.get(
    "/tracks/{track_id}/waveform", operation_id="get_track_waveform", responses=responses(404)
)
def get_track_waveform(
    track_id: int, session: SessionDep, res: Literal["lo", "hi"] = "lo"
) -> WaveformOut:
    """Forma de undă: `lo` (1000 de puncte, panoul piesei), `hi` (8000, editorul de tranziție)."""
    _get_track(session, track_id)
    waveform = session.get(Waveform, track_id)
    if waveform is None:
        raise ApiError(404, "waveform_not_ready", "Forma de undă apare după analiza piesei.")
    return WaveformOut(peaks=list(waveform.peaks if res == "lo" else waveform.peaks_hi))


@router.get(
    "/tracks/{track_id}/clip",
    operation_id="get_track_clip",
    response_class=Response,
    responses={**responses(404, 422), 200: {"content": {"audio/wav": {}}}},
)
def get_track_clip(
    track_id: int,
    session: SessionDep,
    start_s: Annotated[float, Field(ge=0)],
    end_s: Annotated[float, Field(gt=0)],
) -> Response:
    """O bucată din piesă (WAV, 44,1 kHz), pentru previzualizarea unei tranziții."""
    track = _get_track(session, track_id)
    if end_s <= start_s or end_s - start_s > MAX_CLIP_S:
        raise ApiError(422, "bad_clip", f"Bucata trebuie să aibă între 0 și {MAX_CLIP_S:.0f} s.")
    try:
        wav = render_clip(Path(track.path), start_s, min(end_s, track.duration_s))
    except FileNotFoundError as exc:
        raise ApiError(404, "file_missing", f"Fișierul nu mai există: {track.path}") from exc
    return Response(content=wav, media_type="audio/wav")
