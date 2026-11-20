"""Raportul unui mix: eticheta fiecărei tranziții, curba de energie și avertismentele.

Folosește `music/compat.py` și `music/energy_curve.py`; nu are reguli proprii.
"""

from dataclasses import dataclass

from mixmatch.db.models import Track
from mixmatch.music.compat import Label, Match, Problem, TrackInfo, match
from mixmatch.music.energy_curve import EnergyShape, next_target, target_curve


@dataclass(frozen=True)
class TransitionReport:
    position: int  # poziția lui B (1 = tranziția dintre piesele 1 și 2, numărând de la 0)
    from_track_id: int
    to_track_id: int
    match: Match | None  # None dacă una din piese nu e analizată


@dataclass(frozen=True)
class EnergyPoint:
    track_id: int
    actual: int | None
    target: float | None


@dataclass(frozen=True)
class Warning:
    position: int
    problem: Problem
    message: str


@dataclass(frozen=True)
class MixReport:
    transitions: list[TransitionReport]
    energy: list[EnergyPoint]
    next_target_energy: float | None
    warnings: list[Warning]


def _bpm(value: float) -> str:
    return f"{value:.1f}".replace(".", ",").removesuffix(",0")


def _warning(position: int, a: Track, b: Track, result: Match) -> Warning | None:
    if result.label != Label.caution or result.problem is None:
        return None
    if result.problem == Problem.key:
        message = (
            f"Între „{a.title}” ({a.key_camelot}) și „{b.title}” ({b.key_camelot}) tonalitățile "
            "se ciocnesc. Poți schimba piesa sau folosi o tranziție scurtă cu ecou."
        )
    elif result.problem == Problem.tempo:
        message = (
            f"Între „{a.title}” ({_bpm(a.bpm or 0)} BPM) și „{b.title}” ({_bpm(b.bpm or 0)} BPM) "
            f"tempo-ul e prea departe ({_bpm(round(result.tempo_diff_pct, 1))} %). Poți schimba "
            "piesa sau folosi o tăietură pe beat."
        )
    else:
        message = (
            f"Între „{a.title}” și „{b.title}” energia sare de la {a.energy_effective} la "
            f"{b.energy_effective}. Poți pune între ele o piesă de energie intermediară."
        )
    return Warning(position=position, problem=result.problem, message=message)


def build_report(tracks: list[Track], shape: EnergyShape) -> MixReport:
    transitions, warnings = [], []
    for position in range(1, len(tracks)):
        a, b = tracks[position - 1], tracks[position]
        info_a, info_b = TrackInfo.of(a), TrackInfo.of(b)
        result = match(info_a, info_b) if info_a and info_b else None
        transitions.append(TransitionReport(position, a.id, b.id, result))
        if result and (warning := _warning(position, a, b, result)):
            warnings.append(warning)

    targets = target_curve(shape, len(tracks)) or [None] * len(tracks)
    energy = [
        EnergyPoint(track_id=t.id, actual=t.energy_effective, target=target)
        for t, target in zip(tracks, targets, strict=True)
    ]
    return MixReport(
        transitions=transitions,
        energy=energy,
        next_target_energy=next_target(shape, len(tracks)),
        warnings=warnings,
    )
