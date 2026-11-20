from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mixmatch.analysis.runner import (
    _save,
    analyze_pending,
    pending_track_ids,
    start_analysis_if_needed,
)
from mixmatch.analysis.track import analyze_file
from mixmatch.config import settings
from mixmatch.db.models import Job, JobKind, JobStatus, LibraryFolder, Track, Waveform
from mixmatch.jobs import JobQueue
from mixmatch.library.scan import scan_folder
from tests.audio import make_audio, make_music

# Toleranța pentru clipurile sintetice: Essentia lucrează pe cadre de 512 eșantioane, deci la
# tempo mare are pași de ~1–2 BPM (174 iese 172,3). Pe muzică reală e mult mai precis.
BPM_TOLERANCE = 2.0

CASES = [  # bpm, frecvența tonicii, minor, Camelot așteptat
    (128, 220.0, True, "8A"),  # La minor
    (124, 261.63, False, "8B"),  # Do major
    (140, 329.63, True, "9A"),  # Mi minor
    (174, 196.0, False, "9B"),  # Sol major
]


@pytest.fixture(scope="module")
def songs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    root = tmp_path_factory.mktemp("songs")
    return {
        code: make_music(root / f"{code}.wav", bpm, hz, minor) for bpm, hz, minor, code in CASES
    }


@pytest.mark.parametrize(("bpm", "hz", "minor", "code"), CASES)
def test_detects_tempo_and_key(
    songs: dict[str, Path], bpm: float, hz: float, minor: bool, code: str
) -> None:
    result = analyze_file(songs[code])
    assert result.error is None
    assert result.bpm == pytest.approx(bpm, abs=BPM_TOLERANCE)
    assert result.key_camelot == code
    assert result.energy in range(1, 6)
    assert result.loudness_lufs is not None and -40 < result.loudness_lufs < 0
    assert result.peaks is not None and len(result.peaks.hi) == 8000
    if bpm < 160:  # la ~174 BPM grila e decalată de eroarea de tempo (vezi nota pasului 3a)
        assert result.first_beat_s == pytest.approx(0.5, abs=0.06)  # primul kick e la 0,5 s


def test_broken_file_gives_error_not_exception(tmp_path: Path) -> None:
    broken = tmp_path / "stricat.mp3"
    broken.write_bytes(b"\0" * 2048)
    result = analyze_file(broken)
    assert result.error
    assert (result.bpm, result.key_camelot) == (None, None)


def add_tracks(sessions: sessionmaker[Session], *paths: Path) -> None:
    with sessions.begin() as session:
        for path in paths:
            session.add(Track(path=str(path), file_hash=path.name, title=path.stem, duration_s=30))


def test_analyze_pending_saves_results(
    songs: dict[str, Path], tmp_path: Path, sessions: sessionmaker[Session]
) -> None:
    broken = tmp_path / "stricat.wav"
    broken.write_bytes(b"RIFF")
    add_tracks(sessions, songs["8A"], songs["9B"], broken)
    progress: list[float] = []

    assert analyze_pending(sessions, progress.append, workers=2) == 3

    with sessions() as session:
        tracks = {Path(t.path).name: t for t in session.scalars(select(Track))}
        assert tracks["8A.wav"].key_camelot == "8A"
        assert tracks["9B.wav"].bpm == pytest.approx(174, abs=BPM_TOLERANCE)
        assert tracks["stricat.wav"].bpm is None
        assert tracks["8A.wav"].energy is not None
        assert session.get(Waveform, tracks["8A.wav"].id) is not None
        assert session.get(Waveform, tracks["stricat.wav"].id) is None
        # Și piesa stricată e marcată ca analizată, ca să nu fie reluată la nesfârșit.
        assert {t.analysis_version for t in tracks.values()} == {settings.analysis_version}
        assert all(t.analyzed_at for t in tracks.values())
        assert pending_track_ids(session) == []
    assert progress[-1] == 1.0
    assert progress == sorted(progress)


def test_result_is_not_saved_on_a_reused_id(
    songs: dict[str, Path], sessions: sessionmaker[Session]
) -> None:
    add_tracks(sessions, songs["8A"])
    with sessions() as session:
        track = session.scalars(select(Track)).one()
        _save(session, track.id, "/alt/fisier.wav", analyze_file(songs["9B"]))
    with sessions() as session:
        assert session.scalars(select(Track)).one().key_camelot is None


def test_old_analysis_version_is_pending(sessions: sessionmaker[Session], tmp_path: Path) -> None:
    with sessions.begin() as session:
        for name, version in (("vechi", settings.analysis_version - 1), ("nou", None)):
            session.add(
                Track(
                    path=str(tmp_path / name),
                    file_hash=name,
                    title=name,
                    duration_s=30,
                    analysis_version=version,
                )
            )
        session.add(
            Track(
                path=str(tmp_path / "la-zi"),
                file_hash="x",
                title="x",
                duration_s=30,
                analysis_version=settings.analysis_version,
            )
        )
    with sessions() as session:
        assert len(pending_track_ids(session)) == 2


def test_changed_file_is_analyzed_again(tmp_path: Path, sessions: sessionmaker[Session]) -> None:
    song = make_audio(tmp_path / "a.mp3", duration_s=2)
    with sessions.begin() as session:
        folder = LibraryFolder(path=str(tmp_path))
        session.add(folder)
        session.flush()
        folder_id = folder.id
    scan_folder(folder_id, sessions, lambda _: None, min_duration_s=1)
    with sessions.begin() as session:
        session.scalars(select(Track)).one().analysis_version = settings.analysis_version

    scan_folder(folder_id, sessions, lambda _: None, min_duration_s=1)  # neschimbat
    with sessions() as session:
        assert pending_track_ids(session) == []

    make_audio(song, duration_s=3)  # alt conținut
    scan_folder(folder_id, sessions, lambda _: None, min_duration_s=1)
    with sessions() as session:
        assert len(pending_track_ids(session)) == 1


def test_start_analysis_only_when_needed(
    songs: dict[str, Path], sessions: sessionmaker[Session]
) -> None:
    queue = JobQueue(sessions, max_workers=1)
    try:
        assert start_analysis_if_needed(queue, sessions) is None  # nimic de analizat

        with sessions.begin() as session:
            session.add(Job(kind=JobKind.analysis, status=JobStatus.running))
        add_tracks(sessions, songs["8B"])
        assert start_analysis_if_needed(queue, sessions) is None  # rulează deja una

        with sessions.begin() as session:
            session.scalars(select(Job)).one().status = JobStatus.done
        assert start_analysis_if_needed(queue, sessions) is not None
    finally:
        queue.shutdown()
