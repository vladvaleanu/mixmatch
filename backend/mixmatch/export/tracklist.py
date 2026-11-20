"""Tracklistul (text) și fișierul .cue ale unui export, din momentele de început ale pieselor."""

from dataclasses import dataclass

CUE_FRAMES_PER_S = 75  # standardul .cue: minute:secunde:cadre, 75 de cadre pe secundă


@dataclass(frozen=True)
class Entry:
    title: str
    artist: str | None
    start_s: float


def clock(seconds: float) -> str:
    """125 → „2:05”; 3725 → „1:02:05”."""
    total = max(0, int(seconds))
    h, m, s = total // 3600, total % 3600 // 60, total % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def cue_index(seconds: float) -> str:
    """Momentul în formatul .cue: MM:SS:FF (minutele pot trece de 59)."""
    frames = round(max(0.0, seconds) * CUE_FRAMES_PER_S)
    m, rest = divmod(frames, 60 * CUE_FRAMES_PER_S)
    s, f = divmod(rest, CUE_FRAMES_PER_S)
    return f"{m:02d}:{s:02d}:{f:02d}"


def tracklist(mix_name: str, entries: list[Entry]) -> str:
    lines = [mix_name, ""]
    for i, e in enumerate(entries, start=1):
        who = f"{e.artist} — " if e.artist else ""
        lines.append(f"{i:02d}. [{clock(e.start_s)}] {who}{e.title}")
    return "\n".join(lines) + "\n"


def _quote(text: str) -> str:
    return text.replace('"', "'")


def cue_sheet(mix_name: str, audio_file: str, fmt: str, entries: list[Entry]) -> str:
    kind = "MP3" if fmt == "mp3" else "WAVE"
    lines = [f'TITLE "{_quote(mix_name)}"', f'FILE "{_quote(audio_file)}" {kind}']
    for i, e in enumerate(entries, start=1):
        lines += [f"  TRACK {i:02d} AUDIO", f'    TITLE "{_quote(e.title)}"']
        if e.artist:
            lines.append(f'    PERFORMER "{_quote(e.artist)}"')
        lines.append(f"    INDEX 01 {cue_index(e.start_s)}")
    return "\n".join(lines) + "\n"
