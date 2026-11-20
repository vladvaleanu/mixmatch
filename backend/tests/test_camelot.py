import pytest

from mixmatch.music.camelot import classic_name, from_pitch_class, parse, to_camelot

# Roata completă, din tabelul standard Camelot.
WHEEL = {
    "1A": ("G#", "minor"), "2A": ("Eb", "minor"), "3A": ("Bb", "minor"), "4A": ("F", "minor"),
    "5A": ("C", "minor"), "6A": ("G", "minor"), "7A": ("D", "minor"), "8A": ("A", "minor"),
    "9A": ("E", "minor"), "10A": ("B", "minor"), "11A": ("F#", "minor"), "12A": ("C#", "minor"),
    "1B": ("B", "major"), "2B": ("F#", "major"), "3B": ("Db", "major"), "4B": ("Ab", "major"),
    "5B": ("Eb", "major"), "6B": ("Bb", "major"), "7B": ("F", "major"), "8B": ("C", "major"),
    "9B": ("G", "major"), "10B": ("D", "major"), "11B": ("A", "major"), "12B": ("E", "major"),
}  # fmt: skip


@pytest.mark.parametrize(("code", "key"), WHEEL.items())
def test_whole_wheel(code: str, key: tuple[str, str]) -> None:
    assert to_camelot(*key) == code


@pytest.mark.parametrize(
    ("a", "b"), [("Ab", "G#"), ("D#", "Eb"), ("A#", "Bb"), ("Gb", "F#"), ("Db", "C#")]
)
@pytest.mark.parametrize("scale", ["major", "minor"])
def test_enharmonic_spellings_agree(a: str, b: str, scale: str) -> None:
    assert to_camelot(a, scale) == to_camelot(b, scale)


def test_relative_keys_share_the_number() -> None:
    assert to_camelot("A", "minor") == "8A"
    assert to_camelot("C", "major") == "8B"


def test_pitch_class_order() -> None:
    assert [from_pitch_class(pc, minor=False) for pc in (0, 7, 2)] == ["8B", "9B", "10B"]
    assert from_pitch_class(9, minor=True) == "8A"


@pytest.mark.parametrize("bad", [("H", "minor"), ("A", "dorian"), ("", "major")])
def test_unknown_key_raises(bad: tuple[str, str]) -> None:
    with pytest.raises(ValueError):
        to_camelot(*bad)


def test_classic_names() -> None:
    assert classic_name("8A") == "La minor"
    assert classic_name("8B") == "Do major"
    assert classic_name("1A") == "Sol♯ minor"
    assert classic_name("6B") == "Si♭ major"
    assert len({classic_name(code) for code in WHEEL}) == 24


@pytest.mark.parametrize("bad", ["0A", "13B", "8C", "A8", "8a", ""])
def test_parse_rejects_bad_codes(bad: str) -> None:
    with pytest.raises(ValueError):
        parse(bad)
