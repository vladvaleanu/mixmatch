import pytest

from mixmatch.music.camelot import shift
from mixmatch.music.compat import Label, TrackInfo, key_relation, match, semitones

S, G, C = Label.smooth, Label.good, Label.caution
ALL_CODES = [f"{n}{letter}" for n in range(1, 13) for letter in "AB"]


def step(code: str, delta: int, letter: str | None = None) -> str:
    number, own = int(code[:-1]), code[-1]
    return f"{(number - 1 + delta) % 12 + 1}{letter or own}"


def expected_relation(a: str, b: str) -> Label:
    """Roata Camelot, scrisă independent de implementare."""
    if b in (a, step(a, 1), step(a, -1), step(a, 0, "B" if a[-1] == "A" else "A")):
        return S
    if b in (step(a, 2), step(a, -2)):
        return G
    if (a[-1] == "A" and b == step(a, 1, "B")) or (a[-1] == "B" and b == step(a, -1, "A")):
        return G
    return C


@pytest.mark.parametrize("a", ALL_CODES)
def test_every_pair_on_the_wheel(a: str) -> None:
    for b in ALL_CODES:
        assert key_relation(a, b)[0] == expected_relation(a, b), (a, b)


@pytest.mark.parametrize(
    ("a", "b", "label"),
    [
        ("8A", "8A", S),  # același ton
        ("8A", "9A", S),  # +1
        ("8A", "7A", S),  # −1
        ("12A", "1A", S),  # ocolul 12 → 1
        ("1B", "12B", S),  # ocolul 1 → 12
        ("8A", "8B", S),  # relativul
        ("8B", "8A", S),
        ("8A", "9B", G),  # diagonala minor → major
        ("8B", "7A", G),  # diagonala major → minor
        ("8A", "7B", C),  # diagonala „greșită”
        ("8A", "10A", G),  # +2
        ("11A", "1A", G),  # +2 peste ocol
        ("8A", "3B", C),
        ("8A", "2A", C),  # tritonul
    ],
)
def test_named_relations(a: str, b: str, label: Label) -> None:
    assert key_relation(a, b)[0] == label


def test_relations_rank_by_quality() -> None:
    same, fifth, boost, clash = (key_relation("8A", b)[1] for b in ("8A", "9A", "10A", "3A"))
    assert same > fifth > boost > clash == 0


def test_shift_by_semitones() -> None:
    assert shift("8A", 0) == "8A"
    assert shift("8A", 1) == "3A"  # La minor → Si♭ minor
    assert shift("8A", -1) == "1A"  # La minor → Sol♯ minor
    assert shift("8B", 12) == "8B"


@pytest.mark.parametrize(("speed", "expected"), [(1.0, 0), (1.02, 0), (1.03, 1), (0.97, -1)])
def test_semitones_from_speed(speed: float, expected: int) -> None:
    assert semitones(speed) == expected


def info(bpm: float, key: str = "8A", energy: int | None = None) -> TrackInfo:
    return TrackInfo(bpm=bpm, key_camelot=key, energy=energy)


@pytest.mark.parametrize(
    ("b_bpm", "label"),
    [(124.0, S), (121.0, S), (127.5, S), (119.0, G), (130.0, G), (115.0, C), (135.0, C)],
)
def test_tempo_thresholds(b_bpm: float, label: Label) -> None:
    # Tonul ales ca să rămână compatibil după transpunere: izolăm doar tempo-ul.
    a = info(124.0)
    b_key = shift("8A", -semitones(124.0 / b_bpm))
    assert match(a, info(b_bpm, b_key)).label == label


def test_half_and_double_tempo() -> None:
    hiphop, dnb = info(87.0, "5A"), info(174.0, "5A")
    forward, backward = match(hiphop, dnb), match(dnb, hiphop)
    assert (forward.label, forward.speed) == (S, 1.0)
    assert "tempo dublu" in forward.reason
    assert "jumătate de tempo" in backward.reason


def test_vinyl_sync_moves_the_key() -> None:
    # La +4 % (B urcă ~0,7 semitonuri), același ton devine 3A: se ciocnește.
    result = match(info(124.0, "8A"), info(119.2, "8A"))
    assert result.key_after_sync == "3A"
    assert result.label == C
    assert "sincronizat: 3A" in result.reason
    # Aceeași diferență, dar tonul care urcă exact în 8A: sună bine.
    assert match(info(124.0, "8A"), info(119.2, "1A")).key_after_sync == "8A"


@pytest.mark.parametrize(("b_energy", "label"), [(3, S), (4, S), (5, G), (1, G), (6, C)])
def test_energy_jump(b_energy: int, label: Label) -> None:
    assert match(info(124, energy=3), info(124, energy=b_energy)).label == label


def test_missing_energy_is_ignored() -> None:
    assert match(info(124, energy=1), info(124)).label == S


def test_label_is_the_worst_part() -> None:
    # Ton perfect, tempo bun (5 %), energie bună: „Bun”.
    a, b = info(124.0, "8A", 3), info(118.1, shift("8A", -1), 5)
    assert match(a, b).label == G


def test_reason_text() -> None:
    assert (
        match(info(124, "8A", 3), info(123, "9A", 4)).reason == "8A → 9A · −1 BPM · energie 3 → 4"
    )
    assert match(info(124, "8A"), info(124, "8B")).reason == "8A → 8B · același tempo"
    assert match(info(124, "8A"), info(125.5, "8A")).reason == "8A → 8A · +1,5 BPM"


def test_score_orders_better_matches_first() -> None:
    a = info(124, "8A", 3)
    perfect, fifth, boost = (match(a, info(124, k, 3)).score for k in ("8A", "9A", "10A"))
    slower = match(a, info(121, "8A", 3)).score
    assert perfect == 100
    assert perfect > fifth > boost
    assert perfect > slower


def test_track_info_needs_analysis() -> None:
    class Fake:
        def __init__(self, bpm: float | None, key: str | None) -> None:
            self.bpm, self.key_camelot, self.energy_effective = bpm, key, 3

    assert TrackInfo.of(Fake(None, "8A")) is None
    assert TrackInfo.of(Fake(124, None)) is None
    assert TrackInfo.of(Fake(124, "8A")) == TrackInfo(124, "8A", 3)


def test_problem_prefers_tempo_over_the_key_it_breaks() -> None:
    # +28 %: tonul se strică din cauza accelerării; problema reală e tempo-ul.
    result = match(info(122.0, "4A"), info(156.0, "4A"))
    assert result.label == C
    assert result.problem == "tempo"


def test_problem_is_the_key_when_tempo_is_fine() -> None:
    assert match(info(124.0, "8A"), info(124.0, "3B")).problem == "key"


def test_no_problem_without_caution() -> None:
    assert match(info(124.0, "8A"), info(124.0, "9A")).problem is None
