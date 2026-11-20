import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Înainte de orice import din mixmatch: aplicația nu are voie să atingă data/ din repo.
os.environ.setdefault("MIXMATCH_DATA_DIR", tempfile.mkdtemp(prefix="mixmatch-test-"))
os.environ.setdefault("MIXMATCH_EXPORT_DIR", tempfile.mkdtemp(prefix="mixmatch-exports-"))
os.environ.setdefault("MIXMATCH_UPLOAD_DIR", tempfile.mkdtemp(prefix="mixmatch-uploads-"))

import time  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from mixmatch.db.models import (  # noqa: E402
    Collection,
    CollectionTrack,
    Export,
    Job,
    JobStatus,
    LibraryFolder,
    Mix,
    MixItem,
    Track,
    Transition,
    Waveform,
)
from mixmatch.db.session import SessionLocal, create_db_engine, run_migrations  # noqa: E402


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    run_migrations(url)
    return url


@pytest.fixture
def sessions(db_url: str) -> Iterator[sessionmaker[Session]]:
    engine = create_db_engine(db_url)
    yield sessionmaker(engine, expire_on_commit=False)
    engine.dispose()


def wait_for_idle_jobs(timeout_s: float = 60) -> None:
    """Așteaptă joburile pornite de alte teste (ex. analiza după o scanare), ca să nu scrie
    peste datele testului curent."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with SessionLocal() as session:
            busy = session.scalar(
                select(Job.id).where(Job.status.in_([JobStatus.queued, JobStatus.running]))
            )
        if busy is None:
            return
        time.sleep(0.05)
    raise AssertionError("Joburile din teste nu s-au terminat")


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Aplicația, cu lifespan-ul pornit și baza de test goală."""
    from mixmatch.main import app

    with TestClient(app) as test_client:
        wait_for_idle_jobs()
        _clear()
        yield test_client
        wait_for_idle_jobs()
        # Golită și la final: altfel următorul client găsește piese „neanalizate” la pornire și
        # pornește degeaba un job de analiză.
        _clear()


def _clear() -> None:
    with SessionLocal.begin() as session:
        for model in (CollectionTrack, Collection, Export, Transition, MixItem, Mix, Waveform,
                      Track, LibraryFolder, Job):  # fmt: skip
            session.execute(delete(model))
