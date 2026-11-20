"""Analiza unei piese. Rulează în procese separate, deci importă doar ce îi trebuie."""

import logging
from dataclasses import dataclass
from pathlib import Path

from mixmatch.analysis.audio import SAMPLE_RATE, load
from mixmatch.analysis.energy import energy_level, extract_features
from mixmatch.analysis.key import detect_key
from mixmatch.analysis.loudness import integrated_lufs
from mixmatch.analysis.structure import intro_outro_bars
from mixmatch.analysis.tempo import detect_beats
from mixmatch.analysis.waveform import Peaks, compute_peaks

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisResult:
    bpm: float | None = None
    first_beat_s: float | None = None
    key_camelot: str | None = None
    energy: int | None = None
    loudness_lufs: float | None = None
    intro_bars: int | None = None
    outro_bars: int | None = None
    peaks: Peaks | None = None
    beats: list[float] | None = None  # toate beat-urile, cu faza corectată
    error: str | None = None


def analyze_file(path: Path) -> AnalysisResult:
    try:
        audio = load(path)
        if len(audio.mono) == 0:
            return AnalysisResult(error="fișier fără audio")
        mono = audio.mono
        tempo = detect_beats(mono)
        loudness = integrated_lufs(audio)
        energy = None
        structure = None
        if tempo and loudness is not None:
            energy = energy_level(extract_features(mono, loudness, tempo.bpm))
        if tempo:
            structure = intro_outro_bars(mono, SAMPLE_RATE, tempo.bpm, tempo.first_beat_s)
        return AnalysisResult(
            bpm=tempo.bpm if tempo else None,
            first_beat_s=tempo.first_beat_s if tempo else None,
            key_camelot=detect_key(mono),
            energy=energy,
            loudness_lufs=loudness,
            intro_bars=structure[0] if structure else None,
            outro_bars=structure[1] if structure else None,
            peaks=compute_peaks(mono),
            beats=tempo.beats if tempo else None,
        )
    except Exception as exc:  # orice fișier stricat devine un rezultat gol, nu o oprire a jobului
        log.warning("Analiza a eșuat pentru %s: %s", path, exc)
        return AnalysisResult(error=str(exc) or type(exc).__name__)
