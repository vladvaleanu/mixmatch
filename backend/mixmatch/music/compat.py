"""Compatibilitatea a două piese, A urmată de B: eticheta (Lin / Bun / Atenție), scorul și motivul.

Singurul loc cu regulile de compatibilitate. Raportul mixului, sugestiile și ordonarea automată
îl folosesc pe acesta; frontendul doar afișează.

Sincronizarea e stil vinil: B se redă cu viteza `bpm_A / bpm_B` (sau cu jumătate/dublu), deci și
tonul lui B urcă sau coboară. Tonul se judecă după această transpunere.
"""

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from mixmatch.music.camelot import parse, shift

# Pragurile (docs/decisions.md).
TEMPO_SMOOTH_PCT = 3.0
TEMPO_GOOD_PCT = 6.0
ENERGY_SMOOTH_JUMP = 1
ENERGY_GOOD_JUMP = 2
TEMPO_MULTIPLES = (1.0, 2.0, 0.5)  # B la tempo normal, dublu sau jumătate

# Ponderile scorului (0–100), pentru ordonarea sugestiilor.
WEIGHT_KEY, WEIGHT_TEMPO, WEIGHT_ENERGY = 0.5, 0.35, 0.15


class Label(StrEnum):
    smooth = "smooth"  # Lin
    good = "good"  # Bun
    caution = "caution"  # Atenție


_ORDER = [Label.smooth, Label.good, Label.caution]


def label_rank(label: Label) -> int:
    """0 = Lin, 1 = Bun, 2 = Atenție (pentru sortări: Lin înainte de Bun, la orice scor)."""
    return _ORDER.index(label)


def _worst(*labels: Label) -> Label:
    return max(labels, key=_ORDER.index)


class _Analyzed(Protocol):
    bpm: float | None
    key_camelot: str | None

    @property
    def energy_effective(self) -> int | None: ...


@dataclass(frozen=True)
class TrackInfo:
    bpm: float
    key_camelot: str
    energy: int | None = None

    @classmethod
    def of(cls, track: _Analyzed) -> "TrackInfo | None":
        """Din orice piesă cu bpm, ton și energie efectivă; None dacă nu e analizată."""
        if not track.bpm or not track.key_camelot:
            return None
        return cls(bpm=track.bpm, key_camelot=track.key_camelot, energy=track.energy_effective)


@dataclass(frozen=True)
class Match:
    label: Label
    score: int  # 0–100
    reason: str  # „8A → 9A · −1 BPM”
    speed: float  # viteza lui B ca să bată cu A (1.0 = neschimbată)
    key_after_sync: str  # tonul lui B la viteza aceea


@dataclass(frozen=True)
class _Tempo:
    speed: float
    diff_pct: float
    multiple: float


def _tempo(a_bpm: float, b_bpm: float) -> _Tempo:
    multiple = min(TEMPO_MULTIPLES, key=lambda m: abs(math.log(a_bpm / (b_bpm * m))))
    speed = a_bpm / (b_bpm * multiple)
    return _Tempo(speed=speed, diff_pct=abs(speed - 1) * 100, multiple=multiple)


def semitones(speed: float) -> int:
    """Cât se mută tonul la viteza dată, în semitonuri întregi (sub ½ semiton = 0)."""
    return round(12 * math.log2(speed))


def key_relation(a: str, b: str) -> tuple[Label, float]:
    """Relația pe roata Camelot și cât de bine sună (1 = perfect, 0 = se ciocnește)."""
    (na, la), (nb, lb) = parse(a), parse(b)
    step = (nb - na) % 12  # 0–11, în sensul acelor de ceas
    if la == lb:
        if step == 0:
            return Label.smooth, 1.0  # același ton
        if step in (1, 11):
            return Label.smooth, 0.9  # o cvintă
        if step in (2, 10):
            return Label.good, 0.6  # două cvinte („energy boost”)
        return Label.caution, 0.0
    if step == 0:
        return Label.smooth, 0.9  # relativul (8A ↔ 8B)
    if (la, step) in (("A", 1), ("B", 11)):
        return Label.good, 0.6  # diagonala: 8A → 9B, 8B → 7A
    return Label.caution, 0.0


def _tempo_label(diff_pct: float) -> Label:
    if diff_pct <= TEMPO_SMOOTH_PCT:
        return Label.smooth
    return Label.good if diff_pct <= TEMPO_GOOD_PCT else Label.caution


def _energy_label(jump: int) -> Label:
    if jump <= ENERGY_SMOOTH_JUMP:
        return Label.smooth
    return Label.good if jump <= ENERGY_GOOD_JUMP else Label.caution


def _number(value: float) -> str:
    text = f"{abs(value):.1f}".replace(".", ",").removesuffix(",0")
    return ("+" if value > 0 else "−" if value < 0 else "±") + text


def _reason(a: TrackInfo, b: TrackInfo, tempo: _Tempo, key_after: str) -> str:
    parts = [f"{a.key_camelot} → {b.key_camelot}"]
    if key_after != b.key_camelot:
        parts[0] += f" (sincronizat: {key_after})"
    if tempo.multiple != 1.0:
        parts.append("jumătate de tempo" if tempo.multiple == 2.0 else "tempo dublu")
    delta = round(b.bpm * tempo.multiple - a.bpm, 1)
    parts.append(f"{_number(delta)} BPM" if delta else "același tempo")
    if a.energy is not None and b.energy is not None and a.energy != b.energy:
        parts.append(f"energie {a.energy} → {b.energy}")
    return " · ".join(parts)


def match(a: TrackInfo, b: TrackInfo) -> Match:
    """Cât de bine merge B după A."""
    tempo = _tempo(a.bpm, b.bpm)
    key_after = shift(b.key_camelot, semitones(tempo.speed))
    key_label, key_quality = key_relation(a.key_camelot, key_after)
    labels = [key_label, _tempo_label(tempo.diff_pct)]

    energy_quality = 1.0
    if a.energy is not None and b.energy is not None:
        jump = abs(b.energy - a.energy)
        labels.append(_energy_label(jump))
        energy_quality = max(0.0, 1 - jump / 4)

    tempo_quality = max(0.0, 1 - tempo.diff_pct / (2 * TEMPO_GOOD_PCT))
    score = 100 * (
        WEIGHT_KEY * key_quality + WEIGHT_TEMPO * tempo_quality + WEIGHT_ENERGY * energy_quality
    )
    return Match(
        label=_worst(*labels),
        score=round(score),
        reason=_reason(a, b, tempo, key_after),
        speed=tempo.speed,
        key_after_sync=key_after,
    )
