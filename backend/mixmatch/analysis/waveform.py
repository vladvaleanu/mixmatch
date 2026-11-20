"""Vârfurile formei de undă, în trei rezoluții, ca octeți 0–255 (normalizați la vârful piesei)."""

from dataclasses import dataclass

import numpy as np

PREVIEW_POINTS = 40  # rândul din tabel
LO_POINTS = 1000  # panoul din dreapta
HI_POINTS = 8000  # editorul de tranziție


@dataclass(frozen=True)
class Peaks:
    preview: bytes
    lo: bytes
    hi: bytes


def _peaks(mono: np.ndarray, points: int, top: float) -> bytes:
    usable = len(mono) - len(mono) % points
    if usable == 0:
        return bytes(points)
    bins = np.abs(mono[:usable]).reshape(points, -1).max(axis=1)
    return np.round(np.clip(bins / top, 0, 1) * 255).astype(np.uint8).tobytes()


def compute_peaks(mono: np.ndarray) -> Peaks:
    top = float(np.max(np.abs(mono))) if len(mono) else 0.0
    top = top or 1.0
    return Peaks(
        preview=_peaks(mono, PREVIEW_POINTS, top),
        lo=_peaks(mono, LO_POINTS, top),
        hi=_peaks(mono, HI_POINTS, top),
    )
