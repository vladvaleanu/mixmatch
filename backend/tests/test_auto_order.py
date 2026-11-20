import random

import pytest

from mixmatch.mixes.auto_order import Candidate, auto_order
from mixmatch.music.compat import Label, TrackInfo, match
from mixmatch.music.energy_curve import EnergyShape

KEYS = [f"{n}{letter}" for n in range(1, 13) for letter in "AB"]


def candidates(rows: list[tuple[float, str, int | None]]) -> list[Candidate]:
    return [Candidate(i, TrackInfo(bpm, key, energy)) for i, (bpm, key, energy) in enumerate(rows)]


@pytest.mark.parametrize("seed", range(30))
@pytest.mark.parametrize("shape", list(EnergyShape))
def test_never_worse_and_first_stays(seed: int, shape: EnergyShape) -> None:
    rng = random.Random(seed)
    items = candidates(
        [
            (rng.uniform(118, 130), rng.choice(KEYS), rng.randint(1, 5))
            for _ in range(rng.randint(3, 14))
        ]
    )
    result = auto_order(items, shape)
    assert result.score >= result.original_score
    assert result.order[0] == 0
    assert sorted(result.order) == list(range(len(items)))


def test_shuffled_wheel_becomes_a_chain_of_fifths() -> None:
    items = candidates([(124.0, k, 3) for k in ("8A", "11A", "9A", "12A", "10A")])
    result = auto_order(items, EnergyShape.free)
    keys = [items[i].info.key_camelot for i in result.order]  # type: ignore[union-attr]
    assert keys == ["8A", "9A", "10A", "11A", "12A"]
    infos = [items[i].info for i in result.order]
    assert all(match(a, b).label == Label.smooth for a, b in zip(infos, infos[1:], strict=False))  # type: ignore[arg-type]


def test_rise_puts_energy_in_order() -> None:
    items = candidates([(124.0, "8A", e) for e in (1, 5, 3, 2, 4)])
    result = auto_order(items, EnergyShape.rise)
    energies = [items[i].info.energy for i in result.order]  # type: ignore[union-attr]
    assert energies == [1, 2, 3, 4, 5]


def test_good_order_is_kept() -> None:
    items = candidates([(124.0, k, 3) for k in ("8A", "9A", "10A", "11A")])
    assert auto_order(items, EnergyShape.free).order == [0, 1, 2, 3]


def test_unanalyzed_tracks_still_get_a_place() -> None:
    items = [
        Candidate(0, TrackInfo(124, "8A", 3)),
        Candidate(1, None),
        Candidate(2, TrackInfo(124, "9A", 3)),
    ]
    assert sorted(auto_order(items, EnergyShape.free).order) == [0, 1, 2]


def test_too_short_to_reorder() -> None:
    items = candidates([(124.0, "8A", 3), (124.0, "3B", 3)])
    assert auto_order(items, EnergyShape.free).order == [0, 1]
