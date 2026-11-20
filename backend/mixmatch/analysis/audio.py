"""Citirea audio pentru analiză, cu ffmpeg: stereo (pentru tărie) și mono, la 44,1 kHz.

Analiza, bucățile pentru previzualizare (`library/playback.render_clip`) și exportul decodează
toate cu ffmpeg, deci au aceeași cronologie. Decodorul din Essentia păstrează „amorsarea”
codecurilor (la AAC ~48 ms), pe care ffmpeg o taie: grila de beat-uri ar fi fost decalată.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path

import essentia
import numpy as np

SAMPLE_RATE = 44100

essentia.log.warningActive = False  # Essentia e foarte vorbăreț
essentia.log.infoActive = False


@dataclass(frozen=True)
class Audio:
    mono: np.ndarray  # float32, la SAMPLE_RATE
    stereo: np.ndarray  # (n, 2), float32, la SAMPLE_RATE
    sample_rate: float


def load(path: Path) -> Audio:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
         "-ac", "2", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"],
        capture_output=True,
        check=True,
    ).stdout  # fmt: skip
    stereo = np.frombuffer(raw, dtype="<f4").reshape(-1, 2).copy()
    mono = stereo.mean(axis=1, dtype=np.float32)
    return Audio(mono=mono, stereo=stereo, sample_rate=float(SAMPLE_RATE))
