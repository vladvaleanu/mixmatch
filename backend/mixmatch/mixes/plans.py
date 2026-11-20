"""Planurile tranzițiilor unui mix, din bază: aceleași pentru editor, previzualizare și export."""

import numpy as np
from sqlalchemy.orm import Session

from mixmatch.db.models import BeatGridRow, Mix, Track, Transition
from mixmatch.music.transition_plan import DEFAULT_LENGTH, DEFAULT_STYLE, Plan, Side, build_plan


def side(session: Session, track: Track) -> Side | None:
    """Ce știe planul despre o piesă; None dacă piesa nu e analizată."""
    if not track.bpm or track.first_beat_s is None:
        return None
    grid = session.get(BeatGridRow, track.id)
    beats = tuple(float(b) for b in np.frombuffer(grid.beats, dtype="<f4")) if grid else None
    return Side(
        bpm=track.bpm,
        first_beat_s=track.first_beat_s,
        duration_s=track.duration_s,
        intro_bars=track.intro_bars,
        outro_bars=track.outro_bars,
        loudness_lufs=track.loudness_lufs,
        beats=beats,
    )


def settings_for(session: Session, mix: Mix, a: Track, b: Track) -> Transition | None:
    """Setările salvate pentru perechea A → B din mix (legate de pereche, nu de poziție)."""
    return session.get(Transition, (mix.id, a.id, b.id))


def plan_for(session: Session, mix: Mix, a: Track, b: Track) -> Plan | None:
    """Planul tranziției A → B; None dacă una din piese nu e analizată."""
    side_a, side_b = side(session, a), side(session, b)
    if side_a is None or side_b is None:
        return None
    saved = settings_for(session, mix, a, b)
    return build_plan(
        side_a,
        side_b,
        length_bars=saved.length_bars if saved else DEFAULT_LENGTH,
        style=saved.style if saved else DEFAULT_STYLE,
        a_out_s=saved.a_out_s if saved else None,
        b_in_s=saved.b_in_s if saved else None,
        b_nudge_s=saved.b_nudge_s if saved else 0.0,
    )
