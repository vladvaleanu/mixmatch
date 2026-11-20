"""Citirea audio pentru analiză: stereo la rata originală (pentru tărie) și mono la 44,1 kHz."""

from dataclasses import dataclass
from pathlib import Path

import essentia
import essentia.standard as es
import numpy as np

SAMPLE_RATE = 44100

essentia.log.warningActive = False  # Essentia e foarte vorbăreț la fișiere cu metadate ciudate
essentia.log.infoActive = False


@dataclass(frozen=True)
class Audio:
    mono: np.ndarray  # float32, la SAMPLE_RATE
    stereo: np.ndarray  # (n, 2), la rata originală
    sample_rate: float  # rata originală


def load(path: Path) -> Audio:
    stereo, rate, channels, *_ = es.AudioLoader(filename=str(path))()
    mono = es.MonoMixer()(stereo, channels)
    if rate != SAMPLE_RATE:
        mono = es.Resample(inputSampleRate=rate, outputSampleRate=SAMPLE_RATE)(mono)
    return Audio(mono=mono, stereo=stereo, sample_rate=float(rate))
