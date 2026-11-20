import threading
from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session, sessionmaker

from mixmatch.db.models import Job, JobKind, JobStatus
from mixmatch.jobs import INTERRUPTED, JobQueue, Report


@pytest.fixture
def queue(sessions: sessionmaker[Session]) -> Iterator[JobQueue]:
    q = JobQueue(sessions, max_workers=1)
    yield q
    q.shutdown()


def get_job(sessions: sessionmaker[Session], job_id: int) -> Job:
    with sessions() as session:
        job = session.get(Job, job_id)
        assert job is not None
        return job


def test_successful_job_is_done(queue: JobQueue, sessions: sessionmaker[Session]) -> None:
    seen: list[float] = []
    known = threading.Event()  # jobul poate porni înainte ca `submit` să întoarcă id-ul

    def work(report: Report) -> None:
        known.wait(timeout=5)
        report(0.5)
        seen.append(get_job(sessions, job_id).progress)

    job_id, future = queue.submit(JobKind.scan, work)
    known.set()
    future.result(timeout=5)

    job = get_job(sessions, job_id)
    assert seen == [0.5]
    assert (job.status, job.progress, job.error) == (JobStatus.done, 1.0, None)


def test_failing_job_keeps_error(queue: JobQueue, sessions: sessionmaker[Session]) -> None:
    def work(_report: Report) -> None:
        raise ValueError("fișier stricat")

    job_id, future = queue.submit(JobKind.analysis, work)
    future.result(timeout=5)

    job = get_job(sessions, job_id)
    assert (job.status, job.error) == (JobStatus.failed, "fișier stricat")


def test_job_is_running_while_it_works(queue: JobQueue, sessions: sessionmaker[Session]) -> None:
    started, release = threading.Event(), threading.Event()

    def work(_report: Report) -> None:
        started.set()
        release.wait(timeout=5)

    job_id, future = queue.submit(JobKind.export, work)
    assert started.wait(timeout=5)
    assert get_job(sessions, job_id).status is JobStatus.running
    release.set()
    future.result(timeout=5)


def test_progress_is_clamped(queue: JobQueue, sessions: sessionmaker[Session]) -> None:
    seen: list[float] = []
    known = threading.Event()

    def work(report: Report) -> None:
        known.wait(timeout=5)
        report(1.7)
        seen.append(get_job(sessions, job_id).progress)
        report(-1)
        seen.append(get_job(sessions, job_id).progress)

    job_id, future = queue.submit(JobKind.scan, work)
    known.set()
    future.result(timeout=5)
    assert seen == [1.0, 0.0]


def test_unfinished_jobs_fail_after_restart(
    queue: JobQueue, sessions: sessionmaker[Session]
) -> None:
    with sessions.begin() as session:
        session.add_all(
            [
                Job(kind=JobKind.scan, status=JobStatus.running),
                Job(kind=JobKind.scan, status=JobStatus.queued),
                Job(kind=JobKind.scan, status=JobStatus.done),
            ]
        )

    assert queue.fail_interrupted() == 2
    with sessions() as session:
        statuses = [(j.status, j.error) for j in session.query(Job).order_by(Job.id)]
    assert statuses == [
        (JobStatus.failed, INTERRUPTED),
        (JobStatus.failed, INTERRUPTED),
        (JobStatus.done, None),
    ]
