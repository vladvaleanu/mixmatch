"""Citirea audio pentru analiză: mono, 44,1 kHz, float32."""

from pathlib import Path

import essentia
import essentia.standard as es
import numpy as np

SAMPLE_RATE = 44100

essentia.log.warningActive = False  # Essentia e foarte vorbăreț la fișiere cu metadate ciudate
essentia.log.infoActive = False


def load_mono(path: Path) -> np.ndarray:
    return es.MonoLoader(filename=str(path), sampleRate=SAMPLE_RATE)()
