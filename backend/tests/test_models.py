import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mixmatch.db.models import Job, JobKind, JobStatus, LibraryFolder, Track, Waveform


def make_track(**overrides: object) -> Track:
    values: dict[str, object] = {
        "path": "/muzica/a.flac",
        "file_hash": "abc",
        "title": "Paper Lights",
        "duration_s": 312.5,
    }
    values.update(overrides)
    return Track(**values)


def test_track_roundtrip(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        session.add(make_track(artist="Oda Kray", bpm=124.0, key_camelot="8A", energy=4))
    with sessions() as session:
        track = session.query(Track).one()
        assert (track.title, track.bpm, track.key_camelot, track.energy) == (
            "Paper Lights",
            124.0,
            "8A",
            4,
        )
        assert track.energy_manual is None


def test_track_path_is_unique(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        session.add(make_track())
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(make_track(file_hash="other"))


@pytest.mark.parametrize("field", ["energy", "energy_manual"])
@pytest.mark.parametrize("value", [0, 6])
def test_energy_must_be_1_to_5(sessions: sessionmaker[Session], field: str, value: int) -> None:
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(make_track(**{field: value}))


def test_library_folder_path_is_unique(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        session.add(LibraryFolder(path="/muzica"))
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(LibraryFolder(path="/muzica"))


def test_job_defaults(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        session.add(Job(kind=JobKind.scan))
    with sessions() as session:
        job = session.query(Job).one()
        assert job.status is JobStatus.queued
        assert job.progress == 0.0
        assert job.created_at is not None


def test_effective_energy_prefers_manual(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        session.add_all(
            [
                make_track(path="/a", energy=2),
                make_track(path="/b", energy=2, energy_manual=5),
                make_track(path="/c"),
            ]
        )
    with sessions() as session:
        tracks = {t.path: t for t in session.scalars(select(Track))}
        assert [tracks[p].energy_effective for p in ("/a", "/b", "/c")] == [2, 5, None]
        # Aceeași regulă și în SQL, pentru filtre.
        high = session.scalars(select(Track.path).where(Track.energy_effective >= 5)).all()
        assert high == ["/b"]


def test_deleting_track_deletes_waveform(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        track = make_track()
        session.add(track)
        session.flush()
        session.add(Waveform(track_id=track.id, preview=b"1", peaks=b"2", peaks_hi=b"3"))
    with sessions.begin() as session:
        session.delete(session.scalars(select(Track)).one())
    with sessions() as session:
        assert session.scalars(select(Waveform)).all() == []
