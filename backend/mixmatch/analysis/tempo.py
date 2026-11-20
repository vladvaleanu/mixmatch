"""Tempo și grila de beat-uri.

Beat-urile vin din RhythmExtractor2013 (metoda multifeature) din Essentia, apoi se corectează
faza: la multe piese house/techno detectorul se prinde de contratimp (hi-hat, bas), adică grila
stă la jumătate de beat de kick. Comparăm energia de kick din jurul grilei cu cea din jurul
contratimpului și, dacă e mai mare acolo, mutăm toată grila cu jumătate de beat.

Măsurat față de grilele AutoGrid din Traktor (80 de piese, `tools/evaluate_beatgrid.py`):
pe beat 20 → 35, pe contratimp 34 → 13.
"""

from dataclasses import dataclass

import essentia.standard as es
import numpy as np

SAMPLE_RATE = 44100
HOP = 88  # cadre de 2 ms pentru plicul kick-ului
KICK_BAND_HZ = (40.0, 100.0)
KICK_WINDOW_S = 0.04  # căutăm lovitura în ±40 ms în jurul fiecărui beat


@dataclass(frozen=True)
class BeatGrid:
    bpm: float  # tempo-ul global, o zecimală (pentru afișare și compatibilitate)
    beats: list[float]  # toate beat-urile, în secunde, cu faza corectată
    confidence: float  # 0–5,32 la Essentia; peste ~3 e sigur
    shifted_half_beat: bool  # grila detectată era pe contratimp

    @property
    def first_beat_s(self) -> float:
        return round(self.beats[0], 3)


def kick_onsets(audio: np.ndarray) -> np.ndarray:
    """Cât de brusc crește energia din banda kick-ului, pe cadre de 2 ms."""
    low, high = KICK_BAND_HZ
    band = es.BandPass(cutoffFrequency=(low + high) / 2, bandwidth=high - low)(audio)
    frames = len(band) // HOP
    level = np.sqrt((band[: frames * HOP].reshape(frames, HOP).astype(np.float64) ** 2).mean(1))
    return np.maximum(0.0, np.diff(level, prepend=level[0]))


def kick_strength(onsets: np.ndarray, beats: np.ndarray, shift_s: float) -> float:
    """Media celei mai puternice lovituri din jurul fiecărui beat mutat cu `shift_s`."""
    win = int(KICK_WINDOW_S * SAMPLE_RATE / HOP)
    idx = np.round((beats + shift_s) * SAMPLE_RATE / HOP).astype(int)
    idx = idx[(idx > win) & (idx < len(onsets) - win)]
    if len(idx) == 0:
        return 0.0
    windows = np.lib.stride_tricks.sliding_window_view(onsets, 2 * win + 1)
    return float(windows[idx - win].max(axis=1).mean())


def correct_offbeat(beats: np.ndarray, onsets: np.ndarray) -> tuple[np.ndarray, bool]:
    """Mută grila cu jumătate de beat dacă kick-ul e mai puternic pe contratimp."""
    half = float(np.median(np.diff(beats))) / 2
    if kick_strength(onsets, beats, half) > kick_strength(onsets, beats, 0.0):
        shifted = beats + half
        return shifted, True
    return beats, False


def detect_beats(audio: np.ndarray) -> BeatGrid | None:
    bpm, beats, confidence, _, _ = es.RhythmExtractor2013(method="multifeature")(audio)
    if len(beats) < 4 or bpm <= 0:
        return None
    corrected, shifted = correct_offbeat(np.asarray(beats, dtype=np.float64), kick_onsets(audio))
    return BeatGrid(
        bpm=round(float(bpm), 1),
        beats=[round(float(b), 4) for b in corrected],
        confidence=float(confidence),
        shifted_half_beat=shifted,
    )
