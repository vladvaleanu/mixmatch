"""Tempo și primul beat, cu RhythmExtractor2013 (metoda multifeature) din Essentia."""

from dataclasses import dataclass

import essentia.standard as es
import numpy as np


@dataclass(frozen=True)
class Tempo:
    bpm: float  # o zecimală
    first_beat_s: float
    confidence: float  # 0–5,32 la Essentia; peste ~3 e sigur


def detect_tempo(audio: np.ndarray) -> Tempo | None:
    bpm, beats, confidence, _, _ = es.RhythmExtractor2013(method="multifeature")(audio)
    if len(beats) < 2 or bpm <= 0:
        return None
    return Tempo(
        bpm=round(float(bpm), 1),
        first_beat_s=round(float(beats[0]), 3),
        confidence=float(confidence),
    )
