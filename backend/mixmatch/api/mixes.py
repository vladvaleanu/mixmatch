from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.api.tracks import TrackOut
from mixmatch.db.models import Mix, MixItem, Track, Waveform, utcnow
from mixmatch.mixes.report import build_report
from mixmatch.music.compat import Label, Problem
from mixmatch.music.energy_curve import EnergyShape

router = APIRouter(tags=["mixes"])

MixName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
DEFAULT_NAME = "Mix nou"


class MixSummary(BaseModel):
    id: int
    name: str
    track_count: int
    duration_s: float
    updated_at: datetime


class MixOut(BaseModel):
    id: int
    name: str
    energy_shape: EnergyShape
    duration_s: float
    updated_at: datetime
    tracks: list[TrackOut]  # în ordinea din mix


class MixCreate(BaseModel):
    name: MixName = DEFAULT_NAME
    track_ids: list[int] = Field(default_factory=list)


class MixPatch(BaseModel):
    name: MixName | None = None
    energy_shape: EnergyShape | None = None


class MixItemsIn(BaseModel):
    track_ids: list[int]  # ordinea nouă, completă


def _load(session: Session, mix_id: int) -> Mix:
    mix = session.scalar(
        select(Mix)
        .where(Mix.id == mix_id)
        .options(selectinload(Mix.items).selectinload(MixItem.track))
    )
    if mix is None:
        raise ApiError(404, "mix_not_found", f"Mixul {mix_id} nu există")
    return mix


def _out(session: Session, mix: Mix) -> MixOut:
    tracks = [item.track for item in mix.items]
    previews = dict(
        session.execute(
            select(Waveform.track_id, Waveform.preview).where(
                Waveform.track_id.in_([t.id for t in tracks])
            )
        ).all()
    )
    return MixOut(
        id=mix.id,
        name=mix.name,
        energy_shape=mix.energy_shape,
        duration_s=sum(t.duration_s for t in tracks),
        updated_at=mix.updated_at,
        tracks=[TrackOut.from_track(t, previews.get(t.id)) for t in tracks],
    )


def _set_items(session: Session, mix: Mix, track_ids: list[int]) -> None:
    if len(set(track_ids)) != len(track_ids):
        raise ApiError(422, "duplicate_track", "O piesă poate apărea o singură dată într-un mix.")
    known = set(session.scalars(select(Track.id).where(Track.id.in_(track_ids))))
    if missing := [tid for tid in track_ids if tid not in known]:
        raise ApiError(422, "unknown_track", f"Piese inexistente: {missing}")
    # Pozițiile se rescriu complet: șterge, apoi inserează în ordinea nouă.
    session.execute(delete(MixItem).where(MixItem.mix_id == mix.id))
    session.expire(mix, ["items"])
    session.add_all(
        MixItem(mix_id=mix.id, position=i, track_id=tid) for i, tid in enumerate(track_ids)
    )
    mix.updated_at = utcnow()


@router.get("/mixes", operation_id="list_mixes")
def list_mixes(session: SessionDep) -> list[MixSummary]:
    """Mixurile, cele modificate recent primele."""
    rows = session.execute(
        select(
            Mix,
            func.count(MixItem.track_id),
            func.coalesce(func.sum(Track.duration_s), 0.0),
        )
        .outerjoin(MixItem, MixItem.mix_id == Mix.id)
        .outerjoin(Track, Track.id == MixItem.track_id)
        .group_by(Mix.id)
        .order_by(Mix.updated_at.desc(), Mix.id.desc())
    )
    return [
        MixSummary(
            id=mix.id,
            name=mix.name,
            track_count=count,
            duration_s=duration,
            updated_at=mix.updated_at,
        )
        for mix, count, duration in rows
    ]


@router.post("/mixes", status_code=201, operation_id="create_mix", responses=responses(422))
def create_mix(body: MixCreate, session: SessionDep) -> MixOut:
    mix = Mix(name=body.name)
    session.add(mix)
    session.flush()
    _set_items(session, mix, body.track_ids)
    session.commit()
    return _out(session, _load(session, mix.id))


@router.get("/mixes/{mix_id}", operation_id="get_mix", responses=responses(404))
def get_mix(mix_id: int, session: SessionDep) -> MixOut:
    return _out(session, _load(session, mix_id))


@router.patch("/mixes/{mix_id}", operation_id="update_mix", responses=responses(404, 422))
def update_mix(mix_id: int, body: MixPatch, session: SessionDep) -> MixOut:
    mix = _load(session, mix_id)
    if body.name is not None:
        mix.name = body.name
    if body.energy_shape is not None:
        mix.energy_shape = body.energy_shape
    session.commit()
    return _out(session, _load(session, mix_id))


@router.delete(
    "/mixes/{mix_id}", status_code=204, operation_id="delete_mix", responses=responses(404)
)
def delete_mix(mix_id: int, session: SessionDep) -> Response:
    session.delete(_load(session, mix_id))
    session.commit()
    return Response(status_code=204)


@router.put("/mixes/{mix_id}/items", operation_id="set_mix_items", responses=responses(404, 422))
def set_mix_items(mix_id: int, body: MixItemsIn, session: SessionDep) -> MixOut:
    """Salvează ordinea completă a pieselor (adăugare, scoatere și reordonare)."""
    mix = _load(session, mix_id)
    _set_items(session, mix, body.track_ids)
    session.commit()
    return _out(session, _load(session, mix_id))


class TransitionOut(BaseModel):
    position: int  # poziția piesei B (de la 1); tranziția e între pozițiile position−1 și position
    from_track_id: int
    to_track_id: int
    label: Label | None  # None: una din piese nu e analizată
    reason: str | None
    problem: Problem | None


class EnergyPointOut(BaseModel):
    track_id: int
    actual: int | None
    target: float | None  # None pentru forma „Liber”


class WarningOut(BaseModel):
    position: int
    problem: Problem
    message: str


class ReportOut(BaseModel):
    mix_id: int
    track_ids: list[int]  # ordinea pentru care e calculat raportul
    energy_shape: EnergyShape
    transitions: list[TransitionOut]
    energy: list[EnergyPointOut]
    next_target_energy: float | None  # pentru sugestiile „Ce urmează după …”
    warnings: list[WarningOut]


@router.get("/mixes/{mix_id}/report", operation_id="get_mix_report", responses=responses(404))
def get_mix_report(mix_id: int, session: SessionDep) -> ReportOut:
    """Etichetele tranzițiilor, curba de energie (dorită și reală) și avertismentele."""
    mix = _load(session, mix_id)
    tracks = [item.track for item in mix.items]
    report = build_report(tracks, mix.energy_shape)
    return ReportOut(
        mix_id=mix.id,
        track_ids=[t.id for t in tracks],
        energy_shape=mix.energy_shape,
        transitions=[
            TransitionOut(
                position=t.position,
                from_track_id=t.from_track_id,
                to_track_id=t.to_track_id,
                label=t.match.label if t.match else None,
                reason=t.match.reason if t.match else None,
                problem=t.match.problem if t.match else None,
            )
            for t in report.transitions
        ],
        energy=[
            EnergyPointOut(track_id=p.track_id, actual=p.actual, target=p.target)
            for p in report.energy
        ],
        next_target_energy=report.next_target_energy,
        warnings=[
            WarningOut(position=w.position, problem=w.problem, message=w.message)
            for w in report.warnings
        ],
    )
