"""Analiza unei piese. Rulează în procese separate, deci importă doar ce îi trebuie."""

import logging
from dataclasses import dataclass
from pathlib import Path

from mixmatch.analysis.audio import load_mono
from mixmatch.analysis.key import detect_key
from mixmatch.analysis.tempo import detect_tempo

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisResult:
    bpm: float | None = None
    first_beat_s: float | None = None
    key_camelot: str | None = None
    error: str | None = None


def analyze_file(path: Path) -> AnalysisResult:
    try:
        audio = load_mono(path)
        if len(audio) == 0:
            return AnalysisResult(error="fișier fără audio")
        tempo = detect_tempo(audio)
        return AnalysisResult(
            bpm=tempo.bpm if tempo else None,
            first_beat_s=tempo.first_beat_s if tempo else None,
            key_camelot=detect_key(audio),
        )
    except Exception as exc:  # orice fișier stricat devine un rezultat gol, nu o oprire a jobului
        log.warning("Analiza a eșuat pentru %s: %s", path, exc)
        return AnalysisResult(error=str(exc) or type(exc).__name__)
