"""Fișierul pe care îl primește browserul pentru o piesă.

MP3, FLAC, WAV și M4A merg direct. AIFF nu se poate reda în Chrome, așa că se convertește o dată
în FLAC (fără pierderi), în cache, după `file_hash`.
"""

import subprocess
from pathlib import Path

from mixmatch.config import settings

MEDIA_TYPES = {
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
}
NEEDS_CONVERSION = {".aif", ".aiff"}


def playable_file(path: Path, file_hash: str) -> tuple[Path, str]:
    """(fișierul de servit, media type). Ridică FileNotFoundError dacă sursa lipsește."""
    if not path.is_file():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix not in NEEDS_CONVERSION:
        return path, MEDIA_TYPES.get(suffix, "application/octet-stream")

    cached = settings.cache_dir / f"{file_hash}.flac"
    if not cached.is_file():
        cached.parent.mkdir(parents=True, exist_ok=True)
        partial = cached.with_suffix(".partial.flac")
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-map", "0:a", str(partial)],
            check=True,
        )
        partial.replace(cached)  # atomic: o cerere paralelă nu vede un fișier pe jumătate
    return cached, MEDIA_TYPES[".flac"]
