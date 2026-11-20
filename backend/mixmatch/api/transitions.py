from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.api.mixes import load_mix
from mixmatch.api.tracks import TrackOut
from mixmatch.db.models import Mix, Track, Transition, Waveform
from mixmatch.music.compat import Label, Problem, TrackInfo, match
from mixmatch.music.transition_plan import (
    DEFAULT_LENGTH,
    DEFAULT_STYLE,
    Plan,
    Side,
    Style,
    build_plan,
    recommend,
)

router = APIRouter(tags=["transitions"])

LengthBars = Literal[8, 16, 32, 64]


class PointOut(BaseModel):
    t_s: float
    value: float


class EchoTapOut(BaseModel):
    delay_s: float
    gain: float


class AutomationOut(BaseModel):
    target: Literal["a_volume", "b_volume", "a_bass", "b_bass", "a_echo"]
    points: list[PointOut]


class PlanOut(BaseModel):
    """Planul de automatizări (vezi `music/transition_plan.py`): timpii sunt de la începutul
    tranziției; volumul 0–1, basul în dB, ecoul 0–1."""

    style: Style
    length_bars: int
    length_s: float
    a_out_s: float
    b_in_s: float
    a_start_s: float
    b_start_s: float
    speed_b: float
    gain_a_db: float
    gain_b_db: float
    bass_shelf_hz: float
    echo_taps: list[EchoTapOut]
    preview_start_s: float  # fereastra de ascultat, în timpul tranziției (negativ = înainte)
    preview_end_s: float
    automations: list[AutomationOut]
    a_out_auto: bool  # punctul de ieșire e ales automat
    b_in_auto: bool


class TransitionOut(BaseModel):
    mix_id: int
    mix_name: str
    position: int  # poziția lui B (de la 1), ca în raport
    track_count: int
    from_track: TrackOut
    to_track: TrackOut
    label: Label
    reason: str
    problem: Problem | None
    key_label: Label
    tempo_label: Label
    energy_label: Label | None
    key_after_sync: str
    plan: PlanOut


class TransitionPatch(BaseModel):
    length_bars: LengthBars | None = None
    style: Style | None = None
    a_out_s: float | None = Field(default=None, ge=0)
    b_in_s: float | None = Field(default=None, ge=0)
    reset_points: bool = False  # punctele revin la cele alese automat
    auto: bool = (
        False  # „Alege aplicația pentru mine”: lungime și stil după etichetă, puncte automate
    )


def _side(track: Track) -> Side | None:
    if not track.bpm or track.first_beat_s is None:
        return None
    return Side(
        bpm=track.bpm,
        first_beat_s=track.first_beat_s,
        duration_s=track.duration_s,
        intro_bars=track.intro_bars,
        outro_bars=track.outro_bars,
        loudness_lufs=track.loudness_lufs,
    )


def _pair(mix: Mix, position: int) -> tuple[Track, Track]:
    tracks = [item.track for item in mix.items]
    if not 1 <= position < len(tracks):
        raise ApiError(404, "transition_not_found", f"Mixul nu are tranziția {position}.")
    return tracks[position - 1], tracks[position]


def _settings(session: Session, mix: Mix, a: Track, b: Track) -> Transition | None:
    return session.get(Transition, (mix.id, a.id, b.id))


def _out(session: Session, mix: Mix, position: int) -> TransitionOut:
    a, b = _pair(mix, position)
    side_a, side_b, info_a, info_b = _side(a), _side(b), TrackInfo.of(a), TrackInfo.of(b)
    if not (side_a and side_b and info_a and info_b):
        raise ApiError(
            409, "not_analyzed", "Tranziția se poate planifica după analiza ambelor piese."
        )
    saved = _settings(session, mix, a, b)
    plan: Plan = build_plan(
        side_a,
        side_b,
        length_bars=saved.length_bars if saved else DEFAULT_LENGTH,
        style=saved.style if saved else DEFAULT_STYLE,
        a_out_s=saved.a_out_s if saved else None,
        b_in_s=saved.b_in_s if saved else None,
    )
    result = match(info_a, info_b)
    previews = dict(
        session.execute(
            select(Waveform.track_id, Waveform.preview).where(Waveform.track_id.in_([a.id, b.id]))
        ).all()
    )
    return TransitionOut(
        mix_id=mix.id,
        mix_name=mix.name,
        position=position,
        track_count=len(mix.items),
        from_track=TrackOut.from_track(a, previews.get(a.id)),
        to_track=TrackOut.from_track(b, previews.get(b.id)),
        label=result.label,
        reason=result.reason,
        problem=result.problem,
        key_label=result.key_label,
        tempo_label=result.tempo_label,
        energy_label=result.energy_label,
        key_after_sync=result.key_after_sync,
        plan=PlanOut(
            style=plan.style,
            length_bars=plan.length_bars,
            length_s=plan.length_s,
            a_out_s=plan.a_out_s,
            b_in_s=plan.b_in_s,
            a_start_s=plan.a_start_s,
            b_start_s=plan.b_start_s,
            speed_b=plan.speed_b,
            gain_a_db=plan.gain_a_db,
            gain_b_db=plan.gain_b_db,
            bass_shelf_hz=plan.bass_shelf_hz,
            echo_taps=[EchoTapOut(delay_s=e.delay_s, gain=e.gain) for e in plan.echo_taps],
            preview_start_s=plan.preview_start_s,
            preview_end_s=plan.preview_end_s,
            automations=[
                AutomationOut(
                    target=auto.target,  # type: ignore[arg-type]
                    points=[PointOut(t_s=p.t_s, value=p.value) for p in auto.points],
                )
                for auto in plan.automations
            ],
            a_out_auto=saved is None or saved.a_out_s is None,
            b_in_auto=saved is None or saved.b_in_s is None,
        ),
    )


@router.get(
    "/mixes/{mix_id}/transitions/{position}/plan",
    operation_id="get_transition_plan",
    responses=responses(404, 409),
)
def get_transition_plan(mix_id: int, position: int, session: SessionDep) -> TransitionOut:
    """Planul tranziției dintre piesele de pe pozițiile `position − 1` și `position`."""
    return _out(session, load_mix(session, mix_id), position)


@router.patch(
    "/mixes/{mix_id}/transitions/{position}",
    operation_id="update_transition",
    responses=responses(404, 409, 422),
)
def update_transition(
    mix_id: int, position: int, body: TransitionPatch, session: SessionDep
) -> TransitionOut:
    """Lungimea, stilul și punctele de intrare/ieșire (lipite de fraze). Se salvează pe pereche."""
    mix = load_mix(session, mix_id)
    a, b = _pair(mix, position)
    saved = _settings(session, mix, a, b)
    if saved is None:
        saved = Transition(
            mix_id=mix.id,
            from_track_id=a.id,
            to_track_id=b.id,
            length_bars=DEFAULT_LENGTH,
            style=DEFAULT_STYLE,
        )
        session.add(saved)
    if body.auto:
        info_a, info_b = TrackInfo.of(a), TrackInfo.of(b)
        label = match(info_a, info_b).label if info_a and info_b else None
        saved.length_bars, saved.style = recommend(label)
        saved.a_out_s = saved.b_in_s = None
    else:
        if body.length_bars is not None:
            saved.length_bars = body.length_bars
        if body.style is not None:
            saved.style = body.style
        if body.reset_points:
            saved.a_out_s = saved.b_in_s = None
        if body.a_out_s is not None:
            saved.a_out_s = body.a_out_s
        if body.b_in_s is not None:
            saved.b_in_s = body.b_in_s
    session.flush()
    out = _out(session, mix, position)
    # Se salvează valorile lipite de frază, ca un plan recitit să fie identic.
    if saved.a_out_s is not None:
        saved.a_out_s = out.plan.a_out_s
    if saved.b_in_s is not None:
        saved.b_in_s = out.plan.b_in_s
    session.commit()
    return out
