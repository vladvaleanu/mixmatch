"""Tonul, cu KeyExtractor din Essentia, convertit în Camelot."""

import essentia.standard as es
import numpy as np

from mixmatch.music.camelot import to_camelot

# „bgate” a avut cele mai puține tonuri greșite pe 100 de piese din biblioteca utilizatorului,
# comparate cu Traktor (vezi docs/steps/03a-tempo-ton.md).
PROFILE = "bgate"


def detect_key(audio: np.ndarray, profile: str = PROFILE) -> str | None:
    key, scale, strength = es.KeyExtractor(profileType=profile)(audio)
    if strength <= 0:
        return None
    return to_camelot(key, scale)
