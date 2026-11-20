"""Lungimea intro-ului și a outro-ului, în bare (4 beat-uri), de la primul beat.

Intro-ul ține până la prima bară „plină” (tăria aproape de nivelul obișnuit al piesei), outro-ul
de la ultima bară plină până la final. Rezultatul se rotunjește la multiplu de 4 bare.
"""

import numpy as np

BEATS_PER_BAR = 4
FULL_BELOW_P75_DB = 4.0  # o bară e „plină” dacă e cel mult atât sub percentila 75 a pieselor
ROUND_TO_BARS = 4


def bar_levels_db(
    mono: np.ndarray, sample_rate: int, bpm: float, first_beat_s: float
) -> np.ndarray:
    bar = int(BEATS_PER_BAR * 60 / bpm * sample_rate)
    start = int(first_beat_s * sample_rate)
    count = (len(mono) - start) // bar if bar > 0 else 0
    if count <= 0:
        return np.array([])
    bars = mono[start : start + count * bar].reshape(count, bar)
    return 10 * np.log10(np.mean(bars.astype(np.float64) ** 2, axis=1) + 1e-12)


def _round(bars: int) -> int:
    return int(round(bars / ROUND_TO_BARS) * ROUND_TO_BARS)


def intro_outro_bars(
    mono: np.ndarray, sample_rate: int, bpm: float, first_beat_s: float
) -> tuple[int, int] | None:
    levels = bar_levels_db(mono, sample_rate, bpm, first_beat_s)
    if len(levels) < 2 * ROUND_TO_BARS:
        return None
    full = np.flatnonzero(levels >= np.percentile(levels, 75) - FULL_BELOW_P75_DB)
    return _round(int(full[0])), _round(len(levels) - 1 - int(full[-1]))
