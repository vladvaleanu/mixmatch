"""Coada de joburi în proces: un thread pool, cu starea fiecărui job în tabelul `jobs`.

Funcția unui job primește `report(progress)`, cu progress între 0 și 1. Dacă aruncă o excepție,
jobul devine `failed`, iar mesajul ajunge în `error`.
"""

import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from mixmatch.db.models import Job, JobKind, JobStatus
from mixmatch.db.session import SessionLocal

log = logging.getLogger(__name__)

Report = Callable[[float], None]
JobFn = Callable[[Report], None]

INTERRUPTED = "Jobul a fost întrerupt de o repornire a serverului."


class JobQueue:
    def __init__(self, session_factory: sessionmaker[Session], max_workers: int = 2) -> None:
        self._sessions = session_factory
        self._max_workers = max_workers
        self._pool: ThreadPoolExecutor | None = None

    def _executor(self) -> ThreadPoolExecutor:
        # Se creează la nevoie, ca să poată fi refolosit după shutdown (repornirea aplicației).
        if self._pool is None:
            self._pool = ThreadPoolExecutor(self._max_workers, thread_name_prefix="job")
        return self._pool

    def submit(self, kind: JobKind, fn: JobFn) -> tuple[int, Future[None]]:
        with self._sessions.begin() as session:
            job = Job(kind=kind)
            session.add(job)
            session.flush()
            job_id = job.id
        return job_id, self._executor().submit(self._run, job_id, fn)

    def fail_interrupted(self) -> int:
        """Marchează ca eșuate joburile rămase neterminate de la o rulare anterioară."""
        with self._sessions.begin() as session:
            result = session.execute(
                update(Job)
                .where(Job.status.in_([JobStatus.queued, JobStatus.running]))
                .values(status=JobStatus.failed, error=INTERRUPTED)
            )
            return result.rowcount

    def shutdown(self) -> None:
        if self._pool is not None:
            self._pool.shutdown(wait=False, cancel_futures=True)
            self._pool = None

    def _set(self, job_id: int, **values: object) -> None:
        with self._sessions.begin() as session:
            session.execute(update(Job).where(Job.id == job_id).values(**values))

    def _run(self, job_id: int, fn: JobFn) -> None:
        self._set(job_id, status=JobStatus.running)

        def report(progress: float) -> None:
            self._set(job_id, progress=min(max(progress, 0.0), 1.0))

        try:
            fn(report)
        except Exception as exc:
            log.exception("Jobul %s a eșuat", job_id)
            self._set(job_id, status=JobStatus.failed, error=str(exc) or type(exc).__name__)
        else:
            self._set(job_id, status=JobStatus.done, progress=1.0)


queue = JobQueue(SessionLocal)
