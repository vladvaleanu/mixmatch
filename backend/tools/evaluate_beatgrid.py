"""Compară grila de beat-uri a analizei cu grilele AutoGrid din Traktor (pe kick).

    python tools/evaluate_beatgrid.py [câte piese] [nml]

Pentru fiecare piesă: decalajul grilei noastre față de Traktor (ms, adus în ±½ beat) la început,
la mijloc și la final, plus eroarea de tempo. Un decalaj de ~±½ beat = grila e pe contratimp.
Valorile Traktor sunt referința, nu adevărul absolut.
"""

import random
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from mixmatch.config import settings

NML = Path.home() / "Documents/Native Instruments/Traktor 4.0.2/collection.nml"
MUSIC = Path.home() / "Music"
WINDOW_S = 20.0  # cât de lungă e fiecare zonă măsurată


def references(nml: Path) -> list[tuple[str, float, float]]:
    """(cale, BPM Traktor, ancora grilei în secunde) pentru piesele din ~/Music."""
    out = []
    for entry in ET.parse(nml).getroot().iter("ENTRY"):
        loc, tempo, info = entry.find("LOCATION"), entry.find("TEMPO"), entry.find("INFO")
        if loc is None or tempo is None or info is None:
            continue
        path = Path(loc.get("DIR", "").replace("/:", "/") + loc.get("FILE", ""))
        grids = [c for c in entry.findall("CUE_V2") if c.get("TYPE") == "4"]
        if (
            not grids
            or not path.is_relative_to(MUSIC)
            or path.suffix.lower() not in settings.audio_extensions
            or not 120 <= float(info.get("PLAYTIME", "0")) <= 900
            or not path.is_file()
        ):
            continue
        out.append(
            (str(path), float(tempo.get("BPM", "0")), float(grids[0].get("START", "0")) / 1000)
        )
    return out


def measure(item: tuple[str, float, float]) -> dict[str, object] | None:
    from mixmatch.analysis.audio import load
    from mixmatch.analysis.tempo import detect_beats

    path, ref_bpm, anchor = item
    try:
        audio = load(Path(path))
        grid = detect_beats(audio.mono)
    except Exception:
        return None
    if grid is None or len(grid.beats) < 16:
        return None
    beats = np.asarray(grid.beats)
    ref_beat = 60.0 / ref_bpm
    duration = len(audio.mono) / 44100
    zones = {"început": 30.0, "mijloc": duration / 2, "final": duration - 60.0}
    errors = {}
    for name, start in zones.items():
        lines = anchor + ref_beat * np.arange(
            np.ceil((start - anchor) / ref_beat), np.floor((start + WINDOW_S - anchor) / ref_beat)
        )
        if len(lines) < 8:
            continue
        nearest = beats[np.clip(np.searchsorted(beats, lines), 1, len(beats) - 1)]
        before = beats[np.clip(np.searchsorted(beats, lines) - 1, 0, len(beats) - 1)]
        diff = np.where(np.abs(nearest - lines) < np.abs(before - lines), nearest, before) - lines
        wrapped = (diff + ref_beat / 2) % ref_beat - ref_beat / 2
        errors[name] = float(np.median(wrapped) * 1000)
    return {
        "path": path,
        "suffix": Path(path).suffix.lower(),
        "bpm_err": grid.bpm - ref_bpm,
        "beat_ms": ref_beat * 1000,
        **errors,
    }


def verdict(ms: float, beat_ms: float) -> str:
    if abs(ms) <= 15:
        return "pe beat"
    if abs(abs(ms) - beat_ms / 2) <= 30:
        return "contratimp"
    return "decalat"


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    nml = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else NML
    items = references(nml)
    random.Random(8).shuffle(items)
    with ProcessPoolExecutor(settings.analysis_workers) as pool:
        results = [r for r in pool.map(measure, items[:count]) if r]
    by_zone: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in results:
        for zone in ("început", "mijloc", "final"):
            if zone in r:
                by_zone[zone][verdict(r[zone], r["beat_ms"])] += 1  # type: ignore[arg-type]
    formats = dict(sorted(_count(r["suffix"] for r in results).items()))
    print(f"{len(results)} piese (formate: {formats})")
    for zone, counts in by_zone.items():
        total = sum(counts.values())
        print(f"  {zone:8}", {k: f"{v}/{total}" for k, v in sorted(counts.items())})
    errs = np.array([abs(r["bpm_err"]) for r in results])  # type: ignore[arg-type]
    share = np.mean(errs <= 0.05)
    print(f"  tempo: eroare mediană {np.median(errs):.3f} BPM, ≤ 0,05 BPM la {share:.0%}")
    if "-v" in sys.argv:
        for r in results:
            print(f"    {Path(str(r['path'])).name[:40]:40} {r['suffix']:5}",
                  {z: round(r[z]) for z in ("început", "mijloc", "final") if z in r},  # type: ignore[call-overload]
                  f"ΔBPM {r['bpm_err']:+.2f}")  # fmt: skip


def _count(values):  # type: ignore[no-untyped-def]
    out: dict[str, int] = defaultdict(int)
    for v in values:
        out[v] += 1
    return out


if __name__ == "__main__":
    main()
