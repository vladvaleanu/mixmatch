"""Scanarea unui folder: găsește fișierele audio, le citește metadatele și le pune în `tracks`.

O rescanare actualizează piesele existente (după cale), adaugă piesele noi și șterge piesele
ale căror fișiere au dispărut din folder. Nu creează duplicate.
"""

import hashlib
import logging
import os
import re
import struct
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import mutagen
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mixmatch.config import settings
from mixmatch.db.models import LibraryFolder, Track, utcnow

log = logging.getLogger(__name__)

HASH_CHUNK = 64 * 1024
COMMIT_EVERY = 50
_TRACK_NUMBER = re.compile(r"^\s*\d{1,3}\s*[.\-_)]\s*")


@dataclass(frozen=True)
class Metadata:
    title: str
    artist: str | None
    duration_s: float


@dataclass
class ScanResult:
    added: int = 0
    updated: int = 0
    removed: int = 0
    skipped: int = 0


def file_hash(path: Path) -> str:
    """Amprenta rapidă a fișierului: mărimea plus începutul și sfârșitul (nu tot conținutul)."""
    size = path.stat().st_size
    digest = hashlib.sha256(str(size).encode())
    with path.open("rb") as f:
        digest.update(f.read(HASH_CHUNK))
        if size > 2 * HASH_CHUNK:
            f.seek(-HASH_CHUNK, os.SEEK_END)
            digest.update(f.read(HASH_CHUNK))
    return digest.hexdigest()


def _first_tag(tags: object, *keys: str) -> str | None:
    if tags is None:
        return None
    for key in keys:
        try:
            value = tags[key]  # type: ignore[index]
        except (KeyError, ValueError, TypeError):
            continue
        if isinstance(value, list):
            value = value[0] if value else None
        text = str(value).strip() if value is not None else ""
        if text:
            return text
    return None


def _decode(raw: bytes) -> str:
    raw = raw.split(b"\0", 1)[0]
    try:
        return raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        return raw.decode("latin-1").strip()


def riff_info(path: Path) -> dict[str, str]:
    """Tag-urile din chunk-ul LIST/INFO al unui WAV (INAM = titlu, IART = artist).

    Majoritatea WAV-urilor au tag-urile aici, nu în ID3, iar mutagen nu le citește.
    """
    tags: dict[str, str] = {}
    with path.open("rb") as f:
        header = f.read(12)
        if len(header) < 12 or header[:4] != b"RIFF" or header[8:12] != b"WAVE":
            return tags
        while chunk := f.read(8):
            if len(chunk) < 8:
                break
            chunk_id, size = chunk[:4], struct.unpack("<I", chunk[4:])[0]
            if chunk_id == b"LIST" and size >= 4 and f.read(4) == b"INFO":
                body = f.read(size - 4)
                pos = 0
                while pos + 8 <= len(body):
                    sub_id, sub_size = (
                        body[pos : pos + 4],
                        struct.unpack("<I", body[pos + 4 : pos + 8])[0],
                    )
                    value = _decode(body[pos + 8 : pos + 8 + sub_size])
                    if value:
                        tags[sub_id.decode("latin-1")] = value
                    pos += 8 + sub_size + (sub_size & 1)
                if size & 1:
                    f.seek(1, os.SEEK_CUR)
            else:
                consumed = 4 if chunk_id == b"LIST" and size >= 4 else 0
                f.seek(size - consumed + (size & 1), os.SEEK_CUR)
    return tags


def _from_filename(path: Path) -> tuple[str | None, str]:
    """„08. Artist - Titlu.flac” → („Artist”, „Titlu”). Fără „ - ”, titlul e numele fișierului."""
    stem = _TRACK_NUMBER.sub("", path.stem).strip() or path.stem
    artist, sep, title = stem.partition(" - ")
    if sep and artist.strip() and title.strip():
        return artist.strip(), title.strip()
    return None, stem


def read_metadata(path: Path) -> Metadata | None:
    """Titlu, artist și durată. None dacă fișierul nu se poate citi ca audio."""
    try:
        audio = mutagen.File(path, easy=True)
    except (mutagen.MutagenError, OSError) as exc:
        log.warning("Nu pot citi %s: %s", path, exc)
        return None
    if audio is None or audio.info is None or not audio.info.length:
        return None
    # easy=True dă chei simple (title/artist) pentru MP3, FLAC, M4A; WAV/AIFF au cadre ID3,
    # iar WAV-urile au de obicei tag-urile în RIFF INFO.
    tags = audio.tags
    title = _first_tag(tags, "title", "TIT2")
    artist = _first_tag(tags, "artist", "TPE1")
    if path.suffix.lower() == ".wav" and not (title and artist):
        info = riff_info(path)
        title = title or info.get("INAM")
        artist = artist or info.get("IART")
    if not title:
        guessed_artist, title = _from_filename(path)
        artist = artist or guessed_artist
    return Metadata(title=title, artist=artist, duration_s=round(float(audio.info.length), 3))


def find_audio_files(folder: Path) -> list[Path]:
    """Fișierele audio din folder și subfoldere, fără cele ascunse sau de sistem."""
    found = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if not d.startswith((".", "$")))
        for name in sorted(files):
            path = Path(root) / name
            if not name.startswith(".") and path.suffix.lower() in settings.audio_extensions:
                found.append(path)
    return found


def scan_folder(
    folder_id: int,
    sessions: sessionmaker[Session],
    report: Callable[[float], None],
    min_duration_s: float = settings.min_duration_s,
) -> ScanResult:
    result = ScanResult()
    with sessions() as session:
        folder = session.get(LibraryFolder, folder_id)
        if folder is None:
            raise ValueError(f"Folderul {folder_id} nu există")
        root = Path(folder.path)
        if not root.is_dir():
            raise FileNotFoundError(f"Folderul nu mai există pe disc: {root}")

        prefix = str(root).rstrip(os.sep) + os.sep
        existing = {
            t.path: t for t in session.scalars(select(Track).where(Track.path.startswith(prefix)))
        }
        files = find_audio_files(root)
        seen: set[str] = set()

        for index, path in enumerate(files, start=1):
            meta = read_metadata(path)
            if meta is None or meta.duration_s < min_duration_s:
                result.skipped += 1
            else:
                key = str(path)
                seen.add(key)
                values = {
                    "file_hash": file_hash(path),
                    "title": meta.title,
                    "artist": meta.artist,
                    "duration_s": meta.duration_s,
                }
                track = existing.get(key)
                if track is None:
                    session.add(Track(path=key, **values))
                    result.added += 1
                elif any(getattr(track, k) != v for k, v in values.items()):
                    if track.file_hash != values["file_hash"]:
                        track.analysis_version = None  # fișier schimbat → se reanalizează
                    for k, v in values.items():
                        setattr(track, k, v)
                    result.updated += 1
            if index % COMMIT_EVERY == 0:
                session.commit()
                report(index / len(files))

        for path_key, track in existing.items():
            if path_key not in seen:
                session.delete(track)
                result.removed += 1

        folder.last_scan_at = utcnow()
        session.commit()
    report(1.0)
    log.info("Scanare %s: %s", root, result)
    return result
