import numpy as np
import pytest

from mixmatch.analysis.energy import EnergyFeatures, energy_level, score
from mixmatch.analysis.structure import intro_outro_bars
from mixmatch.analysis.waveform import HI_POINTS, LO_POINTS, PREVIEW_POINTS, compute_peaks

RATE = 44100


def features(**overrides: float) -> EnergyFeatures:
    values = {"loudness_lufs": -9.2, "onset_rate": 5.3, "centroid_hz": 3275.0, "bpm": 128.0}
    values.update(overrides)
    return EnergyFeatures(**values)


def test_energy_extremes() -> None:
    calm = features(loudness_lufs=-16, onset_rate=3.5, centroid_hz=1800, bpm=100)
    wild = features(loudness_lufs=-6, onset_rate=7.5, centroid_hz=4700, bpm=145)
    assert energy_level(calm) == 1
    assert energy_level(wild) == 5
    assert energy_level(features()) == 3  # media bibliotecii cade la mijloc


@pytest.mark.parametrize("field", ["loudness_lufs", "onset_rate", "centroid_hz", "bpm"])
def test_energy_grows_with_each_feature(field: str) -> None:
    base = features()
    louder = features(**{field: getattr(base, field) * (0.8 if field == "loudness_lufs" else 1.2)})
    assert score(louder) > score(base)


def test_tempo_octave_errors_are_capped() -> None:
    assert score(features(bpm=256)) == score(features(bpm=150))


def sections(bpm: float, bars: list[tuple[int, float]]) -> np.ndarray:
    """Noise pe bare: [(câte bare, amplitudine), ...], începând de la primul beat (0 s)."""
    bar = int(4 * 60 / bpm * RATE)
    rng = np.random.default_rng(1)
    return np.concatenate([amp * rng.standard_normal(n * bar) for n, amp in bars]).astype("f4")


def test_intro_and_outro_bars() -> None:
    audio = sections(120, [(16, 0.05), (64, 0.5), (8, 0.05)])
    assert intro_outro_bars(audio, RATE, 120, 0.0) == (16, 8)


def test_intro_rounds_to_four_bars() -> None:
    audio = sections(120, [(7, 0.05), (64, 0.5)])
    assert intro_outro_bars(audio, RATE, 120, 0.0) == (8, 0)


def test_too_short_for_structure() -> None:
    assert intro_outro_bars(sections(120, [(4, 0.5)]), RATE, 120, 0.0) is None


def test_peaks_have_three_resolutions() -> None:
    audio = np.sin(np.linspace(0, 400 * np.pi, RATE * 10)).astype("f4") * 0.5
    audio[: RATE * 5] *= 0.1  # prima jumătate mai încet
    peaks = compute_peaks(audio)
    assert (len(peaks.preview), len(peaks.lo), len(peaks.hi)) == (
        PREVIEW_POINTS,
        LO_POINTS,
        HI_POINTS,
    )
    assert max(peaks.lo) == 255  # normalizat la vârful piesei
    assert peaks.preview[0] < 40 < peaks.preview[-1]


def test_peaks_of_silence() -> None:
    assert set(compute_peaks(np.zeros(RATE, dtype="f4")).preview) == {0}
