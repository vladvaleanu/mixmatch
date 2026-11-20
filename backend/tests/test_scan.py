from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mixmatch.db.models import LibraryFolder, Track
from mixmatch.library.scan import ScanResult, read_metadata, scan_folder
from tests.audio import make_audio


@pytest.fixture
def music(tmp_path: Path) -> Path:
    root = tmp_path / "Muzică"
    for ext in ("mp3", "flac", "wav", "aiff", "m4a"):
        make_audio(root / f"tag.{ext}", title=f"Titlu {ext}", artist=f"Artist {ext}")
    make_audio(root / "sub" / "08. Mass Digital - I Know (Original Mix).mp3")
    make_audio(root / "scurt.mp3", duration_s=0.5)
    (root / "note.txt").write_text("nu e audio")
    (root / "._tag.mp3").write_bytes(b"AppleDouble")
    (root / "stricat.mp3").write_bytes(b"\0" * 1000)
    make_audio(root / ".ascuns" / "x.mp3")
    return root


def add_folder(sessions: sessionmaker[Session], path: Path) -> int:
    with sessions.begin() as session:
        folder = LibraryFolder(path=str(path))
        session.add(folder)
        session.flush()
        return folder.id


def scan(sessions: sessionmaker[Session], folder_id: int) -> tuple[ScanResult, list[float]]:
    progress: list[float] = []
    result = scan_folder(folder_id, sessions, progress.append, min_duration_s=1.0)
    return result, progress


def tracks(sessions: sessionmaker[Session]) -> dict[str, Track]:
    with sessions() as session:
        return {Path(t.path).name: t for t in session.scalars(select(Track))}


@pytest.mark.parametrize("ext", ["mp3", "flac", "wav", "aiff", "m4a"])
def test_reads_tags_in_every_format(music: Path, ext: str) -> None:
    meta = read_metadata(music / f"tag.{ext}")
    assert meta is not None
    assert (meta.title, meta.artist) == (f"Titlu {ext}", f"Artist {ext}")
    assert meta.duration_s == pytest.approx(2.0, abs=0.1)


def test_title_and_artist_from_filename_when_untagged(music: Path) -> None:
    meta = read_metadata(music / "sub" / "08. Mass Digital - I Know (Original Mix).mp3")
    assert meta is not None
    assert (meta.artist, meta.title) == ("Mass Digital", "I Know (Original Mix)")


def test_scan_adds_audio_and_skips_the_rest(music: Path, sessions: sessionmaker[Session]) -> None:
    result, progress = scan(sessions, add_folder(sessions, music))

    found = tracks(sessions)
    assert sorted(found) == [
        "08. Mass Digital - I Know (Original Mix).mp3",
        "tag.aiff",
        "tag.flac",
        "tag.m4a",
        "tag.mp3",
        "tag.wav",
    ]
    assert result == ScanResult(added=6, skipped=2)  # scurt.mp3 și stricat.mp3
    assert progress[-1] == 1.0
    assert all(len(t.file_hash) == 64 for t in found.values())
    with sessions() as session:
        assert session.scalars(select(LibraryFolder)).one().last_scan_at is not None


def test_rescan_creates_no_duplicates(music: Path, sessions: sessionmaker[Session]) -> None:
    folder_id = add_folder(sessions, music)
    scan(sessions, folder_id)
    before = {name: t.id for name, t in tracks(sessions).items()}

    result, _ = scan(sessions, folder_id)

    assert result == ScanResult(skipped=2)
    assert {name: t.id for name, t in tracks(sessions).items()} == before


def test_rescan_updates_changed_and_removes_missing(
    music: Path, sessions: sessionmaker[Session]
) -> None:
    folder_id = add_folder(sessions, music)
    scan(sessions, folder_id)
    old = tracks(sessions)

    (music / "tag.flac").unlink()
    make_audio(music / "tag.mp3", duration_s=3.0, title="Titlu nou", artist="Artist mp3")
    make_audio(music / "nou.flac", title="Nouă")
    result, _ = scan(sessions, folder_id)

    found = tracks(sessions)
    assert result == ScanResult(added=1, updated=1, removed=1, skipped=2)
    assert "tag.flac" not in found
    assert found["tag.mp3"].id == old["tag.mp3"].id
    assert found["tag.mp3"].title == "Titlu nou"
    assert found["tag.mp3"].file_hash != old["tag.mp3"].file_hash


def test_scan_leaves_other_folders_alone(tmp_path: Path, sessions: sessionmaker[Session]) -> None:
    make_audio(tmp_path / "A" / "a.mp3")
    make_audio(tmp_path / "AB" / "b.mp3")  # prefix comun cu „A”, dar alt folder
    scan(sessions, add_folder(sessions, tmp_path / "AB"))
    a_id = add_folder(sessions, tmp_path / "A")
    scan(sessions, a_id)

    (tmp_path / "A" / "a.mp3").unlink()
    result, _ = scan(sessions, a_id)

    assert result.removed == 1
    assert sorted(tracks(sessions)) == ["b.mp3"]
