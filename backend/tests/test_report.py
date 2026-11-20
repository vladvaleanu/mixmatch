import pytest

from mixmatch.db.models import Track
from mixmatch.mixes.report import build_report
from mixmatch.music.compat import Label, Problem, TrackInfo, match
from mixmatch.music.energy_curve import EnergyShape, next_target, target_curve


def track(i: int, title: str, bpm: float | None, key: str | None, energy: int | None) -> Track:
    return Track(id=i, path=f"/{i}", file_hash=str(i), title=title, duration_s=300, bpm=bpm,
                 key_camelot=key, energy=energy)  # fmt: skip


def test_curves_have_their_shape() -> None:
    warmup = target_curve(EnergyShape.warmup, 5)
    rise = target_curve(EnergyShape.rise, 7)
    wave = target_curve(EnergyShape.wave, 9)
    assert warmup is not None and rise is not None and wave is not None
    assert (rise[0], rise[-1]) == (2.0, 5.0)
    assert rise == sorted(rise)
    assert warmup == sorted(warmup) and warmup[-1] < rise[-1]  # încălzirea rămâne mai jos
    assert any(b < a for a, b in zip(wave, wave[1:], strict=False))  # valul și coboară
    assert all(1 <= v <= 5 for v in wave)


def test_free_shape_has_no_target() -> None:
    assert target_curve(EnergyShape.free, 5) is None
    assert next_target(EnergyShape.free, 5) is None


def test_next_target_extends_the_curve() -> None:
    assert next_target(EnergyShape.rise, 3) == 5.0  # a 4-a piesă din 4 e finalul urcării
    assert next_target(EnergyShape.rise, 0) == 2.0


def test_report_labels_every_transition() -> None:
    tracks = [
        track(1, "Neon Tide", 122, "8A", 3),
        track(2, "Slow Orbit", 123, "9A", 3),
        track(3, "Concrete Bloom", 125, "9B", 4),
        track(4, "Low Sun", 126, "3B", 5),
    ]
    report = build_report(tracks, EnergyShape.rise)

    labels = [t.match.label if t.match else None for t in report.transitions]
    assert labels == [Label.smooth, Label.smooth, Label.caution]
    assert [t.position for t in report.transitions] == [1, 2, 3]
    assert [(p.actual, p.target) for p in report.energy] == [(3, 2.0), (3, 3.0), (4, 4.0), (5, 5.0)]
    assert len(report.warnings) == 1
    warning = report.warnings[0]
    assert (warning.position, warning.problem) == (3, Problem.key)
    assert "„Concrete Bloom” (9B) și „Low Sun” (3B)" in warning.message


def test_report_uses_the_same_rules_as_compat() -> None:
    a, b = track(1, "A", 124, "8A", 3), track(2, "B", 119.2, "8A", 3)
    report = build_report([a, b], EnergyShape.free)
    direct = match(TrackInfo(124, "8A", 3), TrackInfo(119.2, "8A", 3))
    assert report.transitions[0].match == direct


@pytest.mark.parametrize(
    ("b", "problem", "text"),
    [
        (track(2, "Rapidă", 140, "8A", 3), Problem.tempo, "tempo-ul e prea departe (11,4 %)"),
        (track(2, "Puternică", 124, "8A", 1), Problem.energy, "energia sare de la 4 la 1"),
    ],
)
def test_warning_explains_the_problem(b: Track, problem: Problem, text: str) -> None:
    a = track(1, "Start", 124, "8A", 4)
    warnings = build_report([a, b], EnergyShape.free).warnings
    assert [(w.problem, text in w.message) for w in warnings] == [(problem, True)]


def test_unanalyzed_track_has_no_label() -> None:
    report = build_report([track(1, "A", 124, "8A", 3), track(2, "B", None, None, None)],
                          EnergyShape.free)  # fmt: skip
    assert report.transitions[0].match is None
    assert report.warnings == []
    assert report.energy[1].actual is None


def test_manual_energy_counts() -> None:
    a, b = track(1, "A", 124, "8A", 4), track(2, "B", 124, "8A", 1)
    b.energy_manual = 4
    assert build_report([a, b], EnergyShape.free).warnings == []
