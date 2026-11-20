"""Ordonarea automată a unui mix: o ordine cu tranziții mai bune și mai aproape de curba dorită.

Scorul unei ordini = suma valorilor tranzițiilor (`compat.pair_value`) − abaterea de la curbă
(`compat.curve_cost`). Prima piesă rămâne pe loc. Căutarea: greedy (cea mai bună piesă următoare),
apoi căutare locală (mutări și schimburi) cât timp scorul crește. Ordinea propusă nu e niciodată
mai slabă decât cea de la care pornește.
"""

from dataclasses import dataclass

from mixmatch.music.compat import CURVE_PENALTY, TrackInfo, curve_cost, pair_value
from mixmatch.music.energy_curve import EnergyShape, target_curve

MAX_ROUNDS = 50  # limita căutării locale (în practică se oprește mult mai devreme)


@dataclass(frozen=True)
class Candidate:
    key: int  # identificatorul piesei
    info: TrackInfo | None  # None: piesă neanalizată


@dataclass(frozen=True)
class Ordering:
    order: list[int]  # cheile, în ordinea propusă
    score: float
    original_score: float


class _Scorer:
    def __init__(self, items: list[Candidate], shape: EnergyShape) -> None:
        self.items = items
        self.targets = target_curve(shape, len(items))
        n = len(items)
        self.pairs = [
            [pair_value(items[i].info, items[j].info) for j in range(n)] for i in range(n)
        ]

    def score(self, order: list[int]) -> float:
        transitions = sum(self.pairs[a][b] for a, b in zip(order, order[1:], strict=False))
        energies = [self.items[i].info.energy if self.items[i].info else None for i in order]
        return transitions - curve_cost(energies, self.targets)


def _greedy(scorer: _Scorer, n: int) -> list[int]:
    order, left = [0], set(range(1, n))
    while left:
        position = len(order)

        def gain(j: int, position: int = position) -> float:
            info = scorer.items[j].info
            target = scorer.targets[position] if scorer.targets else None
            known = info is not None and info.energy is not None and target is not None
            off = abs(info.energy - target) if known else 0.0  # type: ignore[operator,union-attr]
            return scorer.pairs[order[-1]][j] - CURVE_PENALTY * off

        best = max(sorted(left), key=gain)
        order.append(best)
        left.remove(best)
    return order


def _improve(scorer: _Scorer, order: list[int]) -> list[int]:
    """Mută sau schimbă câte o piesă (fără prima) cât timp scorul crește."""
    best, best_score = order, scorer.score(order)
    n = len(order)
    for _ in range(MAX_ROUNDS):
        improved = False
        for i in range(1, n):
            for j in range(1, n):
                if i == j:
                    continue
                swapped = best.copy()
                swapped[i], swapped[j] = swapped[j], swapped[i]
                moved = best.copy()
                moved.insert(j, moved.pop(i))
                for candidate in (swapped, moved):
                    candidate_score = scorer.score(candidate)
                    if candidate_score > best_score + 1e-9:
                        best, best_score, improved = candidate, candidate_score, True
        if not improved:
            break
    return best


def auto_order(items: list[Candidate], shape: EnergyShape) -> Ordering:
    """Ordinea propusă pentru `items` (primul rămâne primul)."""
    if len(items) < 3:
        keys = [c.key for c in items]
        return Ordering(order=keys, score=0.0, original_score=0.0)
    scorer = _Scorer(items, shape)
    original = list(range(len(items)))
    original_score = scorer.score(original)
    found = _improve(scorer, _greedy(scorer, len(items)))
    found = _improve(scorer, original) if scorer.score(found) < original_score else found
    if scorer.score(found) < original_score:
        found = original
    return Ordering(
        order=[items[i].key for i in found],
        score=round(scorer.score(found), 1),
        original_score=round(original_score, 1),
    )
