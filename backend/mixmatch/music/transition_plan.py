"""Planul unei tranziții A → B: singura descriere a felului în care sună trecerea.

Browserul (`frontend/src/audio/`) și ffmpeg (`export/`) execută același plan, deci previzualizarea
și exportul sună la fel. Planul nu conține audio, doar momente și valori:

- timpul `t` e în secunde de la începutul tranziției; tranziția durează `length_s`;
- A se redă de la `a_start_s` (în fișierul ei), la viteza ei;
- B se redă de la `b_start_s` (în fișierul ei) la viteza `speed_b` (stil vinil); dacă `b_start_s`
  e negativ, B începe să cânte abia la t = −b_start_s / speed_b;
- automatizările dau volumul (0–1), basul (dB) și ecoul (0–1) pe fiecare deck, cu puncte
  liniare; două puncte cu același `t` = schimbare bruscă;
- basul e un filtru low-shelf la `bass_shelf_hz`; ecoul e o sumă de copii întârziate
  (`echo_taps`: întârziere, volum), alimentată de A după filtru și înainte de volumul ei, și
  trimisă direct la ieșire (coada rămâne după ce A e oprită);
- `preview_start_s` … `preview_end_s` e fereastra de ascultat (câteva bare înainte și după);
- `b_nudge_s` mută B mai târziu (pozitiv) sau mai devreme (negativ) față de A, în timpul mixului:
  corecția manuală când beat-urile nu cad împreună. E deja inclusă în `b_start_s`.
"""

import bisect
import itertools
import math
from dataclasses import dataclass
from enum import StrEnum

from mixmatch.music.compat import Label, sync_speed


class Style(StrEnum):
    eq_swap = "eq_swap"  # Schimb de bas
    crossfade = "crossfade"  # Crossfade simplu
    echo_out = "echo_out"  # Ieșire cu ecou
    cut = "cut"  # Tăietură pe beat


LENGTHS = (8, 16, 32, 64)  # bare
DEFAULT_LENGTH = 16
DEFAULT_STYLE = Style.eq_swap
PHRASE_BARS = 8  # punctele de intrare și ieșire se lipesc de începutul frazelor
BEATS_PER_BAR = 4

# „Alege aplicația pentru mine”: lungimea și stilul după eticheta tranziției.
RECOMMENDED = {
    Label.smooth: (32, Style.eq_swap),
    Label.good: (16, Style.eq_swap),
    Label.caution: (8, Style.echo_out),
}

TARGET_LUFS = -12.0  # auto-gain
GAIN_MIN_DB, GAIN_MAX_DB = -12.0, 6.0
BASS_CUT_DB = -26.0  # basul „scos” la schimbul de bas
ECHO_WET = 0.6
ECHO_FEEDBACK = 0.45  # fiecare repetare e de atâtea ori mai încetă decât precedenta
ECHO_TAPS = 6  # repetări (0,45⁶ ≈ 0,8 %: restul nu se mai aude)
ECHO_BEATS = 0.75  # întârzierea ecoului: trei sferturi de beat
BASS_SHELF_HZ = 150.0
PREVIEW_BARS = 4  # cât se aude înainte și după tranziție, la previzualizare
MIN_LOCAL_BEATS = 8  # sub atâtea beat-uri în fereastră, tempo-ul local nu e de încredere
MAX_LOCAL_DEVIATION = 0.02  # tempo local cu peste 2 % față de cel global = estimare greșită
MAX_NUDGE_S = 1.0  # corecția manuală a lui B, în ambele sensuri
CROSSFADE_STEPS = 8  # puncte pentru curba de putere constantă


@dataclass(frozen=True)
class Side:
    """Ce trebuie știut despre o piesă ca să-i planifici tranziția."""

    bpm: float
    first_beat_s: float
    duration_s: float
    intro_bars: int | None = None
    outro_bars: int | None = None
    loudness_lufs: float | None = None
    # Toate beat-urile detectate (faza pe kick). Cu ele, punctele cad pe beat-uri reale și
    # viteza lui B vine din tempo-ul local, nu din extrapolarea BPM-ului pe toată piesa.
    beats: tuple[float, ...] | None = None


@dataclass(frozen=True)
class Point:
    t_s: float
    value: float


@dataclass(frozen=True)
class Automation:
    target: str  # a_volume, b_volume, a_bass, b_bass, a_echo
    points: list[Point]


@dataclass(frozen=True)
class EchoTap:
    delay_s: float
    gain: float


@dataclass(frozen=True)
class Plan:
    style: Style
    length_bars: int
    length_s: float
    a_out_s: float  # punctul din A unde începe tranziția (lipit de o frază)
    b_in_s: float  # punctul din B care se aude primul (lipit de o frază)
    a_start_s: float  # de unde se redă A la t = 0 (= a_out_s)
    b_start_s: float  # de unde se redă B la t = 0 (poate fi negativ: B încă tace)
    b_nudge_s: float  # corecția manuală, deja aplicată în b_start_s
    speed_b: float
    gain_a_db: float
    gain_b_db: float
    bass_shelf_hz: float
    echo_taps: list[EchoTap]
    preview_start_s: float
    preview_end_s: float
    automations: list[Automation]


def bar_s(bpm: float) -> float:
    return BEATS_PER_BAR * 60.0 / bpm


def total_bars(side: Side) -> int:
    return max(0, int((side.duration_s - side.first_beat_s) // bar_s(side.bpm)))


def on_beat(t_s: float, side: Side) -> float:
    """Cel mai apropiat beat detectat (fără beat-uri: momentul dat)."""
    if not side.beats:
        return round(t_s, 4)
    beats = side.beats
    i = bisect.bisect_left(beats, t_s)
    candidates = beats[max(0, i - 1) : i + 1]
    return round(min(candidates, key=lambda b: abs(b - t_s)), 4)


def local_beat_s(side: Side, start_s: float, end_s: float) -> float | None:
    """Durata unui beat în intervalul dat, din beat-urile detectate (regresie liniară)."""
    if not side.beats:
        return None
    window = [b for b in side.beats if start_s - 0.01 <= b <= end_s]
    if len(window) < MIN_LOCAL_BEATS:
        return None
    gaps = sorted(q - p for p, q in itertools.pairwise(window))
    typical = gaps[len(gaps) // 2]
    index = [round((b - window[0]) / typical) for b in window]
    mean_i = sum(index) / len(index)
    mean_t = sum(window) / len(window)
    num = sum((i - mean_i) * (t - mean_t) for i, t in zip(index, window, strict=True))
    den = sum((i - mean_i) ** 2 for i in index)
    return num / den if den else None


def snap_to_phrase(t_s: float, side: Side) -> float:
    """Cel mai apropiat început de frază (multiplu de 8 bare de la primul beat), pe un beat real."""
    bars = (t_s - side.first_beat_s) / bar_s(side.bpm)
    phrase = round(bars / PHRASE_BARS) * PHRASE_BARS
    phrase = min(max(phrase, 0), total_bars(side) // PHRASE_BARS * PHRASE_BARS)
    return on_beat(side.first_beat_s + phrase * bar_s(side.bpm), side)


def default_a_out(a: Side, length_bars: int) -> float:
    """Tranziția se termină la finalul muzicii lui A și acoperă outro-ul (dacă e mai lung)."""
    start = total_bars(a) - max(a.outro_bars or 0, length_bars)
    start = max(0, start // PHRASE_BARS * PHRASE_BARS)
    return on_beat(a.first_beat_s + start * bar_s(a.bpm), a)


def default_b_in(b: Side) -> float:
    """B intră de la primul beat: intro-ul ei se suprapune peste outro-ul lui A."""
    return round(b.beats[0] if b.beats else b.first_beat_s, 4)


def gain_db(loudness_lufs: float | None) -> float:
    """Auto-gain: câștigul care aduce piesa la tăria țintă."""
    if loudness_lufs is None:
        return 0.0
    return round(min(max(TARGET_LUFS - loudness_lufs, GAIN_MIN_DB), GAIN_MAX_DB), 1)


def fit_length(requested: int, a: Side, b: Side, a_out_s: float, b_in_s: float) -> int:
    """Cea mai lungă variantă ≤ cea cerută care încape în ce a rămas din A și din B."""
    speed = sync_speed(a.bpm, b.bpm)
    a_left = (a.duration_s - a_out_s) / bar_s(a.bpm)
    b_left = (b.duration_s - b_in_s) / speed / bar_s(a.bpm)
    fitting = [n for n in LENGTHS if n <= requested and n <= a_left and n <= b_left]
    return fitting[-1] if fitting else LENGTHS[0]


def echo_taps(bpm: float) -> list[EchoTap]:
    """Repetările ecoului: la fiecare ¾ de beat, fiecare cu 45 % din volumul precedentei."""
    delay = ECHO_BEATS * 60.0 / bpm
    return [
        EchoTap(delay_s=round(delay * k, 4), gain=round(ECHO_FEEDBACK ** (k - 1), 4))
        for k in range(1, ECHO_TAPS + 1)
    ]


def recommend(label: Label | None) -> tuple[int, Style]:
    """Lungimea și stilul recomandate; fără etichetă (piesă neanalizată), valorile implicite."""
    if label is None:
        return DEFAULT_LENGTH, DEFAULT_STYLE
    return RECOMMENDED[label]


def _step(t: float, before: float, after: float) -> list[Point]:
    return [Point(t, before), Point(t, after)]


def _automations(style: Style, length: float) -> tuple[list[Automation], float]:
    """Automatizările stilului și momentul (t) în care B devine audibilă."""
    half = length / 2
    if style == Style.eq_swap:
        return [
            Automation("a_volume", [Point(0, 1), Point(half, 1), Point(length, 0)]),
            Automation("b_volume", [Point(0, 0), Point(half, 1), Point(length, 1)]),
            Automation(
                "a_bass", [Point(0, 0), *_step(half, 0, BASS_CUT_DB), Point(length, BASS_CUT_DB)]
            ),
            Automation(
                "b_bass", [Point(0, BASS_CUT_DB), *_step(half, BASS_CUT_DB, 0), Point(length, 0)]
            ),
        ], 0.0
    if style == Style.crossfade:
        times = [length * i / CROSSFADE_STEPS for i in range(CROSSFADE_STEPS + 1)]
        angle = [math.pi / 2 * i / CROSSFADE_STEPS for i in range(CROSSFADE_STEPS + 1)]
        return [
            Automation(
                "a_volume",
                [Point(t, round(math.cos(x), 4)) for t, x in zip(times, angle, strict=True)],
            ),
            Automation(
                "b_volume",
                [Point(t, round(math.sin(x), 4)) for t, x in zip(times, angle, strict=True)],
            ),
        ], 0.0
    if style == Style.echo_out:
        return [
            Automation("a_volume", [Point(0, 1), *_step(half, 1, 0), Point(length, 0)]),
            Automation("b_volume", [Point(0, 0), *_step(half, 0, 1), Point(length, 1)]),
            # Ecoul se deschide pe prima jumătate; la tăietură se închide intrarea, coada rămâne.
            Automation("a_echo", [Point(0, 0), *_step(half, ECHO_WET, 0), Point(length, 0)]),
        ], half
    return [  # cut: A cântă toată lungimea, apoi B, pe primul timp al frazei
        Automation("a_volume", [Point(0, 1), *_step(length, 1, 0)]),
        Automation("b_volume", [Point(0, 0), *_step(length, 0, 1)]),
    ], length


def _local_sync(
    a: Side, b: Side, a_out: float, b_in: float, length: int, global_speed: float
) -> tuple[float, float]:
    """Viteza lui B și durata unui beat al lui A, din tempo-ul local din fereastra tranziției.

    Cade pe valorile globale dacă lipsesc beat-urile sau estimarea locală pare greșită.
    """
    span_a = length * bar_s(a.bpm)
    beat_a = local_beat_s(a, a_out, a_out + span_a)
    beat_b = local_beat_s(b, b_in, b_in + span_a * global_speed)
    if beat_a is None or beat_b is None:
        return global_speed, 60.0 / a.bpm
    multiple = a.bpm / (b.bpm * global_speed)  # 1, ½ sau 2 (jumătate/dublu)
    speed = beat_b / beat_a / multiple
    if abs(speed / global_speed - 1) > MAX_LOCAL_DEVIATION:
        return global_speed, 60.0 / a.bpm
    return speed, beat_a


def build_plan(
    a: Side,
    b: Side,
    *,
    length_bars: int = DEFAULT_LENGTH,
    style: Style = DEFAULT_STYLE,
    a_out_s: float | None = None,
    b_in_s: float | None = None,
    b_nudge_s: float = 0.0,
) -> Plan:
    """Planul complet. `a_out_s` / `b_in_s` lipsă = puncte alese automat; date = lipite de frază."""
    global_speed = sync_speed(a.bpm, b.bpm)
    nudge = round(min(max(b_nudge_s, -MAX_NUDGE_S), MAX_NUDGE_S), 4)
    b_in = snap_to_phrase(b_in_s, b) if b_in_s is not None else default_b_in(b)
    a_out = snap_to_phrase(a_out_s, a) if a_out_s is not None else default_a_out(a, length_bars)
    length = fit_length(length_bars, a, b, a_out, b_in)
    if a_out_s is None and length != length_bars:
        a_out = default_a_out(a, length)
    speed, beat_a = _local_sync(a, b, a_out, b_in, length, global_speed)
    length_s = round(length * BEATS_PER_BAR * beat_a, 3)
    automations, b_audible_at = _automations(style, length_s)
    return Plan(
        style=style,
        length_bars=length,
        length_s=length_s,
        a_out_s=a_out,
        b_in_s=b_in,
        a_start_s=a_out,
        # B cântă cu `nudge` mai târziu: la t, poziția ei e cea de la t − nudge.
        b_start_s=round(b_in - (b_audible_at + nudge) * speed, 4),
        b_nudge_s=nudge,
        speed_b=round(speed, 5),
        gain_a_db=gain_db(a.loudness_lufs),
        gain_b_db=gain_db(b.loudness_lufs),
        bass_shelf_hz=BASS_SHELF_HZ,
        echo_taps=echo_taps(a.bpm),
        preview_start_s=round(-PREVIEW_BARS * bar_s(a.bpm), 3),
        preview_end_s=round(length_s + PREVIEW_BARS * bar_s(a.bpm), 3),
        automations=automations,
    )
