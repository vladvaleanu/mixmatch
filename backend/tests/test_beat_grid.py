import numpy as np
import pytest

from mixmatch.analysis.tempo import HOP, SAMPLE_RATE, correct_offbeat, kick_strength
from mixmatch.music.transition_plan import Side, build_plan, local_beat_s, on_beat

BEAT = 60 / 124


def onsets_with_kicks(beat_s: float, first_s: float, seconds: float = 60) -> np.ndarray:
    frames = int(seconds * SAMPLE_RATE / HOP)
    onsets = np.zeros(frames)
    for t in np.arange(first_s, seconds - 1, beat_s):
        onsets[int(t * SAMPLE_RATE / HOP)] = 1.0  # lovitura
        onsets[int((t + beat_s / 2) * SAMPLE_RATE / HOP)] = 0.3  # hi-hat-ul de pe contratimp
    return onsets


def test_grid_on_the_offbeat_moves_half_a_beat() -> None:
    onsets = onsets_with_kicks(BEAT, 0.5)
    offbeat = 0.5 + BEAT / 2 + BEAT * np.arange(100)
    corrected, shifted = correct_offbeat(offbeat, onsets)
    assert shifted
    assert corrected[0] == pytest.approx(0.5 + BEAT, abs=0.003)


def test_grid_on_the_kick_stays() -> None:
    onsets = onsets_with_kicks(BEAT, 0.5)
    on_kick = 0.5 + BEAT * np.arange(100)
    corrected, shifted = correct_offbeat(on_kick, onsets)
    assert not shifted
    assert np.array_equal(corrected, on_kick)
    assert kick_strength(onsets, on_kick, 0.0) > kick_strength(onsets, on_kick, BEAT / 2)


# O piesă cu tempo real 124,03, afișată ca 124,0: extrapolarea greșește spre final.
REAL_BEAT = 60 / 124.03
BEATS = tuple(0.5 + REAL_BEAT * i for i in range(740))
A = Side(bpm=124.0, first_beat_s=0.5, duration_s=360.0, outro_bars=32, beats=BEATS)
B = Side(
    bpm=124.0,
    first_beat_s=0.3,
    duration_s=360.0,
    beats=tuple(0.3 + 60 / 123.5 * i for i in range(700)),
)


def test_points_land_on_detected_beats() -> None:
    plan = build_plan(A, B)
    extrapolated = 0.5 + 152 * 4 * 60 / 124.0
    assert plan.a_out_s in {round(b, 4) for b in BEATS}
    assert abs(plan.a_out_s - extrapolated) > 0.05  # extrapolarea ar fi greșit cu ~70 ms
    assert plan.b_in_s == pytest.approx(0.3)


def test_speed_comes_from_the_local_tempo() -> None:
    plan = build_plan(A, B)
    assert plan.speed_b == pytest.approx(124.03 / 123.5, abs=1e-4)
    assert plan.length_s == pytest.approx(16 * 4 * REAL_BEAT, abs=1e-3)


def test_local_tempo_falls_back_when_it_disagrees() -> None:
    wrong = Side(
        bpm=124.0,
        first_beat_s=0.3,
        duration_s=360.0,
        beats=tuple(0.3 + 0.4 * i for i in range(800)),
    )
    assert build_plan(A, wrong).speed_b == pytest.approx(
        1.0, abs=1e-4
    )  # 0,4 s/beat = 150 BPM: absurd


def test_on_beat_and_local_period() -> None:
    assert on_beat(10.0, A) == pytest.approx(min(BEATS, key=lambda b: abs(b - 10.0)), abs=1e-4)
    assert on_beat(10.0, Side(124.0, 0.5, 360.0)) == 10.0
    assert local_beat_s(A, 100, 130) == pytest.approx(REAL_BEAT, abs=1e-6)
    assert local_beat_s(A, 100, 101) is None  # prea puține beat-uri
