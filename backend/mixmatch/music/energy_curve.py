"""Forma dorită a energiei unui set (1–5 pe fiecare poziție), după forma aleasă.

Folosită de raportul mixului (linia punctată), de sugestii și de ordonarea automată.
"""

import math
from enum import StrEnum


class EnergyShape(StrEnum):
    warmup = "warmup"  # Încălzire
    rise = "rise"  # Urcare
    wave = "wave"  # Val
    free = "free"  # Liber


ENERGY_MIN, ENERGY_MAX = 1.0, 5.0


def _at(shape: EnergyShape, t: float) -> float:
    """t = 0 la prima piesă, 1 la ultima."""
    if shape == EnergyShape.warmup:  # Încălzire: pornește jos, urcă ușor
        value = 1.5 + 2.0 * t
    elif shape == EnergyShape.rise:  # Urcare: de la 2 la 5, constant
        value = 2.0 + 3.0 * t
    else:  # Val: urcă, cu două valuri pe drum
        value = 2.5 + 1.5 * t + math.sin(2 * math.pi * 2 * t)
    return round(min(max(value, ENERGY_MIN), ENERGY_MAX), 2)


def target_curve(shape: EnergyShape, count: int) -> list[float] | None:
    """Energia dorită pe fiecare din `count` poziții; None pentru forma „Liber”."""
    if shape == EnergyShape.free or count == 0:
        return None
    if count == 1:
        return [_at(shape, 0.0)]
    return [_at(shape, i / (count - 1)) for i in range(count)]


def next_target(shape: EnergyShape, count: int) -> float | None:
    """Energia dorită pentru o piesă adăugată după cele `count` existente."""
    curve = target_curve(shape, count + 1)
    return curve[-1] if curve else None
