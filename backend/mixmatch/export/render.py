"""Randarea unui mix întreg: execută aceleași planuri de tranziție ca previzualizarea din browser.

- fiecare piesă se decodează cu ffmpeg (aceeași cronologie ca analiza și previzualizarea);
- piesa B a unei tranziții cântă cu `speed_b` (stil vinil) până la `glide_start_s`, apoi revine
  lin la viteza ei în `glide_s`; poziția în fișier se calculează din viteze, eșantioanele se
  interpolează cubic;
- în tranziție: volumul (automatizare × auto-gain), basul (low-shelf, formulele din Web Audio),
  ecoul (aceleași copii întârziate); în afara tranzițiilor, piesa cântă la volum 1, cu
  auto-gain-ul ei;
- mixul se scrie pe bucăți într-un fișier temporar float32, apoi ffmpeg aplică limiter-ul și scrie
  WAV 16-bit / MP3 320 kbps.
"""

import math
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import essentia.standard as es
import numpy as np

from mixmatch.analysis.audio import SAMPLE_RATE, load
from mixmatch.music.transition_plan import Automation, Plan, gain_db

SOLO_BLOCK_S = 20.0  # cât se randează odată dintr-o porțiune cu o singură piesă
LIMIT_LINEAR = 0.891  # −1 dB
FORMATS = {
    "wav": ["-c:a", "pcm_s16le"],
    "mp3": ["-c:a", "libmp3lame", "-b:a", "320k"],
}


@dataclass(frozen=True)
class RenderResult:
    duration_s: float
    track_starts_s: list[float]  # când începe fiecare piesă (mijlocul tranziției spre ea)


class RenderError(Exception):
    """Mixul nu se poate randa (mesajul e pentru utilizator)."""


@dataclass(frozen=True)
class MixTrack:
    title: str
    path: Path
    loudness_lufs: float | None


@dataclass(frozen=True)
class _Segment:
    """Pe [t0, t0 + dur) din mix, piesa pornește de la poziția p0, cu viteza trecând v0 → v1."""

    t0: float
    p0: float
    v0: float
    v1: float
    dur: float

    def position(self, t: np.ndarray) -> np.ndarray:
        tau = t - self.t0
        if self.v0 == self.v1 or math.isinf(self.dur):
            return self.p0 + self.v0 * tau
        return self.p0 + self.v0 * tau + (self.v1 - self.v0) * tau**2 / (2 * self.dur)

    @property
    def end(self) -> float:
        return self.t0 + self.dur

    @property
    def p_end(self) -> float:
        return float(self.position(np.array([self.end]))[0])


class _Timeline:
    """Unde se află o piesă (în secunde de fișier) la fiecare moment al mixului."""

    def __init__(self, segments: list[_Segment]) -> None:
        self.segments = segments

    def position(self, t: np.ndarray) -> np.ndarray:
        out = np.empty_like(t)
        for i, seg in enumerate(self.segments):
            last = i == len(self.segments) - 1
            mask = (t >= seg.t0) & ((t < seg.end) | last)
            out[mask] = seg.position(t[mask])
        before = t < self.segments[0].t0
        out[before] = self.segments[0].position(t[before])
        return out

    def time_at(self, p: float) -> float:
        """Momentul din mix în care piesa ajunge la poziția p."""
        for seg in self.segments:
            if math.isinf(seg.dur) or seg.p_end >= p:
                if seg.v0 == seg.v1 or math.isinf(seg.dur):
                    return seg.t0 + (p - seg.p0) / seg.v0
                a = (seg.v1 - seg.v0) / (2 * seg.dur)
                tau = (-seg.v0 + math.sqrt(seg.v0**2 + 4 * a * (p - seg.p0))) / (2 * a)
                return seg.t0 + tau
        raise RenderError("Poziție în afara piesei.")

    def speed_at(self, t: float) -> float:
        for seg in self.segments:
            if t < seg.end or math.isinf(seg.dur):
                k = 0.0 if math.isinf(seg.dur) else (t - seg.t0) / seg.dur
                return seg.v0 + (seg.v1 - seg.v0) * min(max(k, 0.0), 1.0)
        return self.segments[-1].v1


def _cubic(audio: np.ndarray, pos_s: np.ndarray) -> np.ndarray:
    """Eșantioanele piesei (n, 2) la pozițiile date (s), interpolare Catmull-Rom; 0 în afară."""
    x = pos_s * SAMPLE_RATE
    i = np.floor(x).astype(np.int64)
    f = (x - i)[:, None].astype(np.float32)
    n = len(audio)
    valid = (i >= 0) & (i < n)  # vecinii de la margini se repetă (clip mai jos)

    def at(k: np.ndarray) -> np.ndarray:
        return audio[np.clip(k, 0, n - 1)]

    p0, p1, p2, p3 = at(i - 1), at(i), at(i + 1), at(i + 2)
    out = 0.5 * (
        2 * p1
        + (p2 - p0) * f
        + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f**2
        + (3 * p1 - p0 - 3 * p2 + p3) * f**3
    )
    out[~valid] = 0.0
    return out.astype(np.float32)


def _automation(auto: Automation | None, t: np.ndarray, fallback: float) -> np.ndarray:
    """Valorile unei automatizări la momentele t (relative la începutul tranziției)."""
    if auto is None:
        return np.full(len(t), fallback, dtype=np.float32)
    xs = [p.t_s for p in auto.points]
    # Două puncte la același moment = salt: al doilea se mută imperceptibil mai târziu.
    for k in range(1, len(xs)):
        if xs[k] <= xs[k - 1]:
            xs[k] = xs[k - 1] + 1e-7
    return np.interp(t, xs, [p.value for p in auto.points]).astype(np.float32)


def lowshelf(gain_db_value: float, freq_hz: float) -> tuple[list[float], list[float]]:
    """Coeficienții unui filtru low-shelf, ca în specificația Web Audio (RBJ, S = 1)."""
    a = 10 ** (gain_db_value / 40)
    w0 = 2 * math.pi * freq_hz / SAMPLE_RATE
    cos_w, alpha = math.cos(w0), math.sin(w0) / 2 * math.sqrt(2)
    sq = 2 * math.sqrt(a) * alpha
    b0 = a * ((a + 1) - (a - 1) * cos_w + sq)
    b1 = 2 * a * ((a - 1) - (a + 1) * cos_w)
    b2 = a * ((a + 1) - (a - 1) * cos_w - sq)
    a0 = (a + 1) + (a - 1) * cos_w + sq
    a1 = -2 * ((a - 1) + (a + 1) * cos_w)
    a2 = (a + 1) + (a - 1) * cos_w - sq
    return [b0 / a0, b1 / a0, b2 / a0], [1.0, a1 / a0, a2 / a0]


def _filter(signal: np.ndarray, gain_db_value: float, freq_hz: float) -> np.ndarray:
    num, den = lowshelf(gain_db_value, freq_hz)
    out = np.empty_like(signal)
    for ch in range(signal.shape[1]):
        out[:, ch] = es.IIR(numerator=num, denominator=den)(np.ascontiguousarray(signal[:, ch]))
    return out


def _bass(signal: np.ndarray, auto: Automation | None, t: np.ndarray, freq_hz: float) -> np.ndarray:
    """Aplică automatizarea de bas: între semnalul neatins și cel filtrat la nivelul minim."""
    if auto is None:
        return signal
    values = _automation(auto, t, 0.0)
    floor = min(p.value for p in auto.points)
    if floor >= 0:
        return signal
    wet = _filter(signal, floor, freq_hz)
    w = np.clip(values / floor, 0.0, 1.0)[:, None]
    return (signal * (1 - w) + wet * w).astype(np.float32)


def _timelines(tracks: list[MixTrack], plans: list[Plan]) -> tuple[list[_Timeline], list[float]]:
    """Cronologia fiecărei piese și momentul din mix în care începe fiecare tranziție."""
    timelines = [_Timeline([_Segment(0.0, 0.0, 1.0, 1.0, math.inf)])]
    starts = []
    for j, plan in enumerate(plans):
        a = timelines[j]
        start = a.time_at(plan.a_start_s)
        if starts and start < starts[-1] + plans[j - 1].length_s:
            raise RenderError(
                f"„{tracks[j].title}” e prea scurtă pentru tranzițiile alese. "
                "Alege o tranziție mai scurtă sau un punct de ieșire mai târziu."
            )
        if abs(a.speed_at(start) - 1) > 1e-6:
            raise RenderError(
                f"„{tracks[j].title}” nu apucă să revină la viteza ei "
                "înainte de tranziția următoare."
            )
        starts.append(start)
        s, glide = plan.speed_b, plan.glide_s
        p_glide = plan.b_start_s + s * plan.glide_start_s
        p_after = p_glide + (s + 1) / 2 * glide
        timelines.append(
            _Timeline(
                [
                    _Segment(start, plan.b_start_s, s, s, plan.glide_start_s),
                    _Segment(start + plan.glide_start_s, p_glide, s, 1.0, glide),
                    _Segment(start + plan.glide_start_s + glide, p_after, 1.0, 1.0, math.inf),
                ]
            )
        )
    return timelines, starts


def render_mix(
    tracks: list[MixTrack],
    plans: list[Plan],
    out_path: Path,
    fmt: str,
    report: Callable[[float], None] = lambda _: None,
    limiter: bool = True,
) -> RenderResult:
    """Randează mixul în `out_path`. Întoarce durata și momentul de început al fiecărei piese."""
    if not tracks:
        raise RenderError("Mixul e gol.")
    if len(plans) != len(tracks) - 1:
        raise RenderError("Lipsesc planurile unor tranziții.")
    timelines, starts = _timelines(tracks, plans)
    gains = [
        plans[i].gain_a_db
        if i < len(plans)
        else (plans[i - 1].gain_b_db if plans else gain_db(t.loudness_lufs))
        for i, t in enumerate(tracks)
    ]
    levels = [10 ** (g / 20) for g in gains]
    decoded: dict[int, np.ndarray] = {}

    def audio(i: int) -> np.ndarray:
        if i not in decoded:
            for old in [k for k in decoded if k < i - 1]:
                del decoded[old]  # în memorie stau cel mult două piese
            decoded[i] = load(tracks[i].path).stereo
        return decoded[i]

    last = len(tracks) - 1
    end_time = (
        timelines[last].time_at(len(audio(last)) / SAMPLE_RATE)
        if last
        else len(audio(0)) / SAMPLE_RATE
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        raw_path = Path(tmp) / "mix.f32"
        with raw_path.open("wb") as raw:

            def solo(i: int, t_from: float, t_to: float) -> None:
                t = t_from
                while t < t_to:
                    block_end = min(t + SOLO_BLOCK_S, t_to)
                    times = t + np.arange(int(round((block_end - t) * SAMPLE_RATE))) / SAMPLE_RATE
                    if len(times):
                        out = _cubic(audio(i), timelines[i].position(times)) * levels[i]
                        raw.write(out.astype("<f4").tobytes())
                    t = block_end
                    report(min(t / end_time, 1.0) * 0.95)

            cursor = 0.0
            for j, plan in enumerate(plans):
                solo(j, cursor, starts[j])
                tail = max((tap.delay_s for tap in plan.echo_taps), default=0.0)
                has_echo = any(a.target == "a_echo" for a in plan.automations)
                t_end = starts[j] + plan.length_s + (tail if has_echo else 0.0)
                cursor = _transition(raw, plan, starts[j], t_end, j, timelines, levels, audio)
                report(min(cursor / end_time, 1.0) * 0.95)
            solo(last, cursor, end_time)

        afilter = [f"alimiter=limit={LIMIT_LINEAR}:level=false"] if limiter else ["anull"]
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "2",
             "-i", str(raw_path), "-af", *afilter, *FORMATS[fmt], str(out_path)],
            check=True,
            capture_output=True,
        )  # fmt: skip
    report(1.0)
    return RenderResult(
        duration_s=end_time,
        track_starts_s=[0.0]
        + [start + plan.length_s / 2 for start, plan in zip(starts, plans, strict=True)],
    )


def _transition(
    raw,  # type: ignore[no-untyped-def]
    plan: Plan,
    start: float,
    t_end: float,
    j: int,
    timelines: list[_Timeline],
    levels: list[float],
    audio: Callable[[int], np.ndarray],
) -> float:
    """Randează tranziția j (A = piesa j, B = piesa j + 1) pe [start, t_end). Întoarce t_end."""
    frames = int(round((t_end - start) * SAMPLE_RATE))
    times = start + np.arange(frames) / SAMPLE_RATE
    rel = times - start
    autos = {a.target: a for a in plan.automations}

    deck_a = _cubic(audio(j), timelines[j].position(times))
    deck_b = _cubic(audio(j + 1), timelines[j + 1].position(times))
    deck_a = _bass(deck_a, autos.get("a_bass"), rel, plan.bass_shelf_hz)
    deck_b = _bass(deck_b, autos.get("b_bass"), rel, plan.bass_shelf_hz)

    vol_a = _automation(autos.get("a_volume"), rel, 1.0)[:, None] * levels[j]
    vol_b = _automation(autos.get("b_volume"), rel, 0.0)[:, None] * levels[j + 1]
    out = deck_a * vol_a + deck_b * vol_b

    if "a_echo" in autos:
        send = deck_a * (_automation(autos["a_echo"], rel, 0.0)[:, None] * levels[j])
        for tap in plan.echo_taps:
            shift = int(round(tap.delay_s * SAMPLE_RATE))
            if shift < frames:
                out[shift:] += tap.gain * send[: frames - shift]
    raw.write(out.astype("<f4").tobytes())
    return t_end
