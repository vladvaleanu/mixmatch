"""Măsoară acuratețea analizei față de valorile din Traktor.

    python tools/evaluate_analysis.py pick <collection.nml>  # alege → test-tracks/reference.csv
    python tools/evaluate_analysis.py run                    # analizează și compară

Valorile Traktor sunt tot o estimare: raportul arată acordul cu Traktor, nu adevărul absolut.
"""

import csv
import random
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from mixmatch.analysis.track import analyze_file
from mixmatch.config import REPO_DIR, settings
from mixmatch.music.camelot import from_pitch_class, parse

REFERENCE = REPO_DIR / "test-tracks" / "reference.csv"
HOW_MANY = 20
MUSIC_DIR = Path.home() / "Music"


def pick(nml: Path) -> None:
    """Alege piese existente pe disc, cu BPM și ton, din cât mai multe foldere și formate."""
    by_folder: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in ET.parse(nml).getroot().iter("ENTRY"):
        loc, tempo, key, info = (
            entry.find(t) for t in ("LOCATION", "TEMPO", "MUSICAL_KEY", "INFO")
        )
        if loc is None or tempo is None or key is None or info is None:
            continue
        path = Path(loc.get("DIR", "").replace("/:", "/") + loc.get("FILE", ""))
        playtime = float(info.get("PLAYTIME", "0"))
        if (
            not path.is_relative_to(MUSIC_DIR)
            or path.suffix.lower() not in settings.audio_extensions
            or not path.is_file()
            or not 90 <= playtime <= 900  # fără sample-uri și fără mixuri lungi
        ):
            continue
        value = int(key.get("VALUE", "-1"))
        if not 0 <= value <= 23:
            continue
        camelot = from_pitch_class(
            value % 12, minor=value >= 12
        )  # Traktor: 0–11 major, 12–23 minor
        bpm = round(float(tempo.get("BPM", "0")), 1)
        by_folder[path.parent.name].append({"path": str(path), "bpm": str(bpm), "key": camelot})

    rng = random.Random(42)
    folders = sorted(by_folder)
    rng.shuffle(folders)
    chosen: list[dict[str, str]] = []
    formats: dict[str, int] = defaultdict(int)
    while len(chosen) < HOW_MANY and any(by_folder.values()):
        for folder in folders:
            candidates = by_folder[folder]
            if not candidates or len(chosen) >= HOW_MANY:
                continue
            # Preferă formatul cel mai puțin reprezentat până acum.
            rng.shuffle(candidates)
            candidates.sort(key=lambda c: formats[Path(c["path"]).suffix.lower()])
            row = candidates.pop(0)
            formats[Path(row["path"]).suffix.lower()] += 1
            chosen.append(row)

    REFERENCE.parent.mkdir(exist_ok=True)
    with REFERENCE.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "bpm", "key"])
        writer.writeheader()
        writer.writerows(chosen)
    print(f"{len(chosen)} piese → {REFERENCE}; formate: {dict(formats)}")


def _tempo_verdict(ours: float | None, ref: float) -> str:
    if ours is None:
        return "lipsă"
    if abs(ours - ref) <= 0.5:
        return "exact"
    if any(abs(ours * f - ref) <= 1.0 for f in (2, 0.5, 1.5, 2 / 3)):
        return "octavă"
    return "greșit"


def _key_verdict(ours: str | None, ref: str) -> str:
    if ours is None:
        return "lipsă"
    (n1, l1), (n2, l2) = parse(ours), parse(ref)
    if (n1, l1) == (n2, l2):
        return "exact"
    if n1 == n2:
        return "relativ"
    if l1 == l2 and (n1 - n2) % 12 in (1, 11):
        return "cvintă"
    return "greșit"


def run() -> None:
    rows = list(csv.DictReader(REFERENCE.open()))
    tempo_counts: dict[str, int] = defaultdict(int)
    key_counts: dict[str, int] = defaultdict(int)
    started = time.monotonic()
    for row in rows:
        result = analyze_file(Path(row["path"]))
        tv = _tempo_verdict(result.bpm, float(row["bpm"]))
        kv = _key_verdict(result.key_camelot, row["key"])
        tempo_counts[tv] += 1
        key_counts[kv] += 1
        print(
            f"{Path(row['path']).name[:48]:48}  BPM {row['bpm']:>6} / {result.bpm!s:>6} {tv:7}"
            f"  ton {row['key']:>3} / {result.key_camelot!s:>3} {kv}"
        )
    n = len(rows)
    print(f"\n{n} piese în {time.monotonic() - started:.0f} s")
    print("Tempo:", {k: f"{v}/{n}" for k, v in sorted(tempo_counts.items())})
    print("Ton:  ", {k: f"{v}/{n}" for k, v in sorted(key_counts.items())})


if __name__ == "__main__":
    if sys.argv[1:2] == ["pick"] and len(sys.argv) == 3:
        pick(Path(sys.argv[2]).expanduser())
    elif sys.argv[1:] == ["run"]:
        run()
    else:
        print(__doc__)
        sys.exit(2)
