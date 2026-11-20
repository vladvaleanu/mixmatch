"""Forma de undă, în trei rezoluții, ca octeți 0–255.

Fiecare punct e tăria RMS a intervalului, normalizată la cel mai tare interval. Vârful (maximul) ar
arăta un bloc plin la masterele tari; RMS-ul arată intro-ul, breakdown-urile și drop-urile.
"""

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


def _levels(mono: np.ndarray, points: int) -> bytes:
    usable = len(mono) - len(mono) % points
    if usable == 0:
        return bytes(points)
    rms = np.sqrt(np.mean(mono[:usable].astype(np.float64).reshape(points, -1) ** 2, axis=1))
    top = float(rms.max()) or 1.0
    return np.round(np.clip(rms / top, 0, 1) * 255).astype(np.uint8).tobytes()


def compute_peaks(mono: np.ndarray) -> Peaks:
    return Peaks(
        preview=_levels(mono, PREVIEW_POINTS),
        lo=_levels(mono, LO_POINTS),
        hi=_levels(mono, HI_POINTS),
    )
