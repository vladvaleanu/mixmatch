import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mixmatch.db.models import Job, JobKind, JobStatus, LibraryFolder, Track


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
