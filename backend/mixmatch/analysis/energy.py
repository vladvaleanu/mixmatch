"""Energia 1–5: un scor din tărie, densitatea loviturilor, strălucire și tempo.

Pragurile sunt fixe, calibrate o dată pe biblioteca utilizatorului (vezi CALIBRATION), ca energia
unei piese să nu se schimbe când biblioteca crește.
"""

from dataclasses import dataclass

import essentia.standard as es
import numpy as np

# Calibrare (2026-11-20): 200 de piese aleatorii din ~/Music, din 40+ foldere (minimal house,
# tech house, hardgroove, hip-hop). Media și abaterea fiecărei caracteristici, ponderile și
# pragurile scorului la cvintile (20/40/60/80 %). Nu se recalculează când biblioteca crește.
CALIBRATION = {
    #              medie    abatere  pondere
    "loudness_lufs": (-9.2, 2.33, 0.30),
    "onset_rate": (5.32, 1.05, 0.25),
    "centroid_hz": (3274.8, 785.4, 0.20),
    "bpm": (128.1, 12.88, 0.25),
}
THRESHOLDS = (-0.472, -0.092, 0.205, 0.515)
# Tempo-ul se limitează la acest interval, ca o eroare dublu/jumătate să nu domine scorul.
BPM_RANGE = (90.0, 150.0)


@dataclass(frozen=True)
class EnergyFeatures:
    loudness_lufs: float
    onset_rate: float  # lovituri pe secundă
    centroid_hz: float  # centrul de greutate al spectrului (strălucirea)
    bpm: float


def extract_features(mono: np.ndarray, loudness_lufs: float, bpm: float) -> EnergyFeatures:
    _, onset_rate = es.OnsetRate()(mono)
    window, spectrum = es.Windowing(type="hann"), es.Spectrum()
    centroid = es.Centroid(range=22050)
    # Un cadru din patru ajunge pentru o medie și e de 4 ori mai rapid.
    frames = es.FrameGenerator(mono, frameSize=2048, hopSize=2048 * 4, startFromZero=True)
    centroids = [centroid(spectrum(window(frame))) for frame in frames]
    return EnergyFeatures(
        loudness_lufs=loudness_lufs,
        onset_rate=float(onset_rate),
        centroid_hz=float(np.mean(centroids)) if centroids else 0.0,
        bpm=bpm,
    )


def score(features: EnergyFeatures) -> float:
    values = {
        "loudness_lufs": features.loudness_lufs,
        "onset_rate": features.onset_rate,
        "centroid_hz": features.centroid_hz,
        "bpm": min(max(features.bpm, BPM_RANGE[0]), BPM_RANGE[1]),
    }
    return sum(
        weight * (values[name] - mean) / std for name, (mean, std, weight) in CALIBRATION.items()
    )


def energy_level(features: EnergyFeatures) -> int:
    """Scorul → 1–5, după pragurile fixe."""
    return 1 + sum(score(features) > threshold for threshold in THRESHOLDS)
