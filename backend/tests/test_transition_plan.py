import pytest

from mixmatch.music.compat import Label
from mixmatch.music.transition_plan import (
    BASS_CUT_DB,
    Side,
    Style,
    bar_s,
    build_plan,
    gain_db,
    recommend,
    snap_to_phrase,
)

A = Side(
    bpm=124.0, first_beat_s=0.5, duration_s=360.0, intro_bars=16, outro_bars=32, loudness_lufs=-8.5
)
B = Side(
    bpm=123.0, first_beat_s=0.3, duration_s=400.0, intro_bars=16, outro_bars=16, loudness_lufs=-14.0
)
BAR_A = bar_s(124.0)


def points(plan, target):  # type: ignore[no-untyped-def]
    auto = next(a for a in plan.automations if a.target == target)
    return [(round(p.t_s, 3), p.value) for p in auto.points]


def test_default_plan() -> None:
    plan = build_plan(A, B)
    assert (plan.style, plan.length_bars) == (Style.eq_swap, 16)
    assert plan.length_s == pytest.approx(16 * BAR_A, abs=0.001)
    # 185 de bare în A; outro-ul de 32 începe la bara 153 → fraza 152.
    assert plan.a_out_s == pytest.approx(0.5 + 152 * BAR_A, abs=0.001)
    assert plan.b_in_s == plan.b_start_s == 0.3
    assert plan.speed_b == pytest.approx(124 / 123, abs=1e-5)


def test_auto_gain() -> None:
    plan = build_plan(A, B)
    assert (plan.gain_a_db, plan.gain_b_db) == (-3.5, 2.0)
    assert gain_db(-30) == 6.0  # limitat
    assert gain_db(None) == 0.0


def test_eq_swap_swaps_the_bass_in_the_middle() -> None:
    plan = build_plan(A, B)
    half = round(plan.length_s / 2, 3)
    assert points(plan, "a_bass") == [
        (0, 0),
        (half, 0),
        (half, BASS_CUT_DB),
        (plan.length_s, BASS_CUT_DB),
    ]
    assert points(plan, "b_bass") == [
        (0, BASS_CUT_DB),
        (half, BASS_CUT_DB),
        (half, 0),
        (plan.length_s, 0),
    ]
    assert points(plan, "b_volume")[-1] == (plan.length_s, 1)
    assert points(plan, "a_volume")[-1] == (plan.length_s, 0)


def test_crossfade_keeps_power_constant() -> None:
    plan = build_plan(A, B, style=Style.crossfade)
    a, b = points(plan, "a_volume"), points(plan, "b_volume")
    for (_, va), (_, vb) in zip(a, b, strict=True):
        assert va**2 + vb**2 == pytest.approx(1, abs=1e-3)
    assert {x.target for x in plan.automations} == {"a_volume", "b_volume"}


def test_echo_out_starts_b_at_the_cut() -> None:
    plan = build_plan(A, B, style=Style.echo_out)
    half = plan.length_s / 2
    assert plan.b_start_s == pytest.approx(B.first_beat_s - half * plan.speed_b, abs=0.001)
    assert points(plan, "a_echo")[1] == (round(half, 3), 0.6)
    assert plan.echo_delay_s == pytest.approx(0.75 * 60 / 124, abs=1e-4)


def test_cut_swaps_at_the_end() -> None:
    plan = build_plan(A, B, style=Style.cut)
    assert points(plan, "b_volume")[-2:] == [(plan.length_s, 0), (plan.length_s, 1)]
    assert plan.b_start_s == pytest.approx(B.first_beat_s - plan.length_s * plan.speed_b, abs=0.001)


def test_points_snap_to_phrases() -> None:
    assert snap_to_phrase(100.0, A) == pytest.approx(0.5 + 48 * BAR_A, abs=0.001)  # bara 51 → 48
    assert snap_to_phrase(-5.0, A) == 0.5  # nu înainte de primul beat
    assert snap_to_phrase(10_000.0, A) == pytest.approx(0.5 + 184 * BAR_A, abs=0.001)
    plan = build_plan(A, B, a_out_s=100.0, b_in_s=40.0)
    assert plan.a_out_s == pytest.approx(0.5 + 48 * BAR_A, abs=0.001)
    assert plan.b_in_s == pytest.approx(0.3 + 24 * bar_s(123.0), abs=0.001)  # bara 20,3 → 24


def test_length_shrinks_to_what_is_left() -> None:
    # Ieșirea la 20 de bare de final: 64 nu încape, 16 da.
    near_end = 0.5 + 165 * BAR_A
    plan = build_plan(A, B, length_bars=64, a_out_s=near_end)
    assert plan.length_bars == 16


def test_longer_automatic_transition_starts_earlier() -> None:
    short, long = build_plan(A, B, length_bars=16), build_plan(A, B, length_bars=64)
    assert long.a_out_s < short.a_out_s
    assert long.a_out_s + long.length_s <= A.duration_s


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        (Label.smooth, (32, Style.eq_swap)),
        (Label.good, (16, Style.eq_swap)),
        (Label.caution, (8, Style.echo_out)),
        (None, (16, Style.eq_swap)),
    ],
)
def test_recommend(label: Label | None, expected: tuple[int, Style]) -> None:
    assert recommend(label) == expected


def test_half_tempo_partner() -> None:
    plan = build_plan(Side(87.0, 0.2, 240.0), Side(174.0, 0.1, 300.0))
    assert plan.speed_b == pytest.approx(1.0)
