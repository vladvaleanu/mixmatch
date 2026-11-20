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


def make_music(
    path: Path,
    bpm: float,
    root_hz: float,
    minor: bool,
    duration_s: float = 30.0,
    sample_rate: int = 44100,
) -> Path:
    """O „piesă” sintetică: kick pe fiecare beat peste acordul tonicii (cu bas), scris ca WAV.

    Tempo-ul și tonul sunt cunoscute exact, deci testele analizei nu depind de muzică reală.
    """
    import wave

    import numpy as np

    t = np.arange(int(duration_s * sample_rate)) / sample_rate
    third = 3 if minor else 4
    signal = np.zeros_like(t)
    for semitones, gain in ((-12, 0.5), (0, 0.4), (third, 0.3), (7, 0.3)):
        freq = root_hz * 2 ** (semitones / 12)
        for harmonic in (1, 2, 3):
            signal += gain / harmonic * np.sin(2 * np.pi * freq * harmonic * t)
    signal *= 0.15

    beat = 60.0 / bpm
    kick_len = int(0.12 * sample_rate)
    kt = np.arange(kick_len) / sample_rate
    kick = np.sin(2 * np.pi * (55 + 90 * np.exp(-kt * 40)) * kt) * np.exp(-kt * 25)
    for start in np.arange(0.5, duration_s - 0.2, beat):
        i = int(start * sample_rate)
        signal[i : i + kick_len] += kick[: len(signal) - i]

    pcm = (np.clip(signal / np.max(np.abs(signal)), -1, 1) * 32000).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return path
