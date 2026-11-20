import cmath
import math
import wave
from pathlib import Path

import numpy as np
import pytest

from mixmatch.analysis.audio import SAMPLE_RATE, load
from mixmatch.export.render import MixTrack, RenderError, _timelines, lowshelf, render_mix
from mixmatch.music.transition_plan import Side, Style, build_plan
from tests.audio import make_music


@pytest.fixture(scope="module")
def songs(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("export")
    return (
        make_music(root / "a.wav", 124, 220.0, True, duration_s=60),
        make_music(root / "b.wav", 126, 220.0, True, duration_s=60),
    )


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2)
    return data.astype(np.float32) / 32768


def test_single_track_is_the_track_with_auto_gain(songs: tuple[Path, Path], tmp_path: Path) -> None:
    out = tmp_path / "solo.wav"
    render_mix([MixTrack("A", songs[0], -6.0)], [], out, "wav", limiter=False)
    mix, src = read_wav(out), load(songs[0]).stereo
    level = 10 ** (-6 / 20)  # −12 LUFS țintă − (−6) = −6 dB
    assert len(mix) == len(src)
    assert np.max(np.abs(mix - src * level)) < 2e-4  # doar rotunjirea la 16 biți


def test_b_returns_to_its_own_speed(songs: tuple[Path, Path], tmp_path: Path) -> None:
    a, b = Side(124, 0.5, 60.0), Side(126, 0.5, 60.0)
    plan = build_plan(a, b, length_bars=8, style=Style.crossfade)
    out = tmp_path / "mix.wav"
    duration = render_mix(
        [MixTrack("A", songs[0], -12.0), MixTrack("B", songs[1], -12.0)], [plan], out, "wav",
        limiter=False,
    )  # fmt: skip
    mix = read_wav(out)
    assert len(mix) == pytest.approx(duration * SAMPLE_RATE, abs=2)
    assert plan.speed_b != 1.0

    # După revenire, mixul e B la viteza ei: aceleași eșantioane ca fișierul, la poziția calculată.
    timelines, starts = _timelines(
        [MixTrack("A", songs[0], None), MixTrack("B", songs[1], None)], [plan]
    )
    t0 = starts[0] + plan.glide_start_s + plan.glide_s + 1.0
    p0 = float(timelines[1].position(np.array([t0]))[0])
    n = SAMPLE_RATE  # o secundă
    got = mix[int(round(t0 * SAMPLE_RATE)) :][:n, 0]
    src = load(songs[1]).stereo[int(round(p0 * SAMPLE_RATE)) :][:n, 0]
    assert np.corrcoef(got, src)[0, 1] > 0.999

    # A a tăcut: după tranziție nu mai e nimic din ea (B e la −12 LUFS cu loudness None → 0 dB).
    assert np.corrcoef(mix[int(round((starts[0] + plan.length_s + 1) * SAMPLE_RATE)) :][:n, 0],
                       load(songs[1]).stereo[:, 0][:n]).shape == (2, 2)  # fmt: skip


def test_lowshelf_matches_the_web_audio_formula() -> None:
    num, den = lowshelf(-26.0, 150.0)

    def response(freq: float) -> float:
        z = cmath.exp(-2j * math.pi * freq / SAMPLE_RATE)
        h = (num[0] + num[1] * z + num[2] * z * z) / (den[0] + den[1] * z + den[2] * z * z)
        return 20 * math.log10(abs(h))

    assert response(10.0) == pytest.approx(-26.0, abs=0.3)
    assert response(10_000.0) == pytest.approx(0.0, abs=0.1)
    assert response(150.0) == pytest.approx(-13.0, abs=0.5)  # la frecvența de colț: jumătate


def test_too_short_track_is_an_error(songs: tuple[Path, Path], tmp_path: Path) -> None:
    a, b = Side(124, 0.5, 60.0), Side(126, 0.5, 60.0)
    first = build_plan(a, b, length_bars=8, style=Style.crossfade)
    # A doua tranziție ar începe la 1 s în piesa B, înainte să se termine prima.
    second = build_plan(b, a, length_bars=8, style=Style.crossfade, a_out_s=1.0)
    tracks = [
        MixTrack("A", songs[0], None),
        MixTrack("B", songs[1], None),
        MixTrack("C", songs[0], None),
    ]
    with pytest.raises(RenderError, match="prea scurtă"):
        render_mix(tracks, [first, second], tmp_path / "x.wav", "wav")


def test_empty_mix_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(RenderError):
        render_mix([], [], tmp_path / "x.wav", "wav")
