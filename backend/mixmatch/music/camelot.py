"""Roata Camelot: conversia ton → cod (8A, 8B) și numele clasic al tonului, în română.

1A–12A sunt tonuri minore, 1B–12B majore. Un pas pe roată (±1) = o cvintă.
"""

import re

# Clasele de înălțime, cu toate denumirile pe care le pot da detectoarele.
_PITCH_CLASS = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}  # fmt: skip

# Numele clasic pentru fiecare cifră Camelot, cu ortografia uzuală a fiecărui ton.
_MINOR_NAMES = {
    1: "Sol♯ minor", 2: "Mi♭ minor", 3: "Si♭ minor", 4: "Fa minor",
    5: "Do minor", 6: "Sol minor", 7: "Re minor", 8: "La minor",
    9: "Mi minor", 10: "Si minor", 11: "Fa♯ minor", 12: "Do♯ minor",
}  # fmt: skip
_MAJOR_NAMES = {
    1: "Si major", 2: "Fa♯ major", 3: "Re♭ major", 4: "La♭ major",
    5: "Mi♭ major", 6: "Si♭ major", 7: "Fa major", 8: "Do major",
    9: "Sol major", 10: "Re major", 11: "La major", 12: "Mi major",
}  # fmt: skip

_CODE = re.compile(r"^(1[0-2]|[1-9])([AB])$")


def from_pitch_class(pitch_class: int, minor: bool) -> str:
    """0 = Do, 9 = La. La minor → 8A, Do major → 8B; fiecare cvintă în sus adaugă 1."""
    # Înmulțirea cu 7 transformă semitonurile în pași de cvintă.
    reference = 9 if minor else 0
    number = ((pitch_class - reference) * 7 % 12 + 7) % 12 + 1
    return f"{number}{'A' if minor else 'B'}"


def to_camelot(key: str, scale: str) -> str:
    """("A", "minor") → "8A". Ridică ValueError pentru un ton necunoscut."""
    if key not in _PITCH_CLASS or scale not in ("major", "minor"):
        raise ValueError(f"Ton necunoscut: {key} {scale}")
    return from_pitch_class(_PITCH_CLASS[key], minor=scale == "minor")


def parse(code: str) -> tuple[int, str]:
    """ "8A" → (8, "A")."""
    match = _CODE.match(code)
    if not match:
        raise ValueError(f"Cod Camelot invalid: {code}")
    return int(match.group(1)), match.group(2)


def classic_name(code: str) -> str:
    """ "8A" → "La minor". Doar pentru afișare."""
    number, letter = parse(code)
    return (_MINOR_NAMES if letter == "A" else _MAJOR_NAMES)[number]


def shift(code: str, semitones: int) -> str:
    """Tonul după transpunere: un semiton în sus = 7 pași pe roată (aceeași literă)."""
    number, letter = parse(code)
    return f"{(number - 1 + 7 * semitones) % 12 + 1}{letter}"
