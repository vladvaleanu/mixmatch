"""Fișiere audio mici pentru teste, generate cu ffmpeg."""

import subprocess
from pathlib import Path


def make_audio(
    path: Path,
    duration_s: float = 2.0,
    title: str | None = None,
    artist: str | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi"]
    cmd += ["-i", f"sine=frequency=440:duration={duration_s}"]
    if title:
        cmd += ["-metadata", f"title={title}"]
    if artist:
        cmd += ["-metadata", f"artist={artist}"]
    if path.suffix in (".aif", ".aiff"):
        cmd += ["-write_id3v2", "1"]  # AIFF-urile din magazine au tag-uri ID3
    subprocess.run([*cmd, str(path)], check=True)
    return path
