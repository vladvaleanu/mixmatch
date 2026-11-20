"""Analiza bibliotecii ca job: toate piesele neanalizate (sau analizate cu o versiune veche).

Piesele se analizează în procese separate (Essentia ține procesorul ocupat), iar rezultatele
se scriu în bază din firul jobului, pe măsură ce vin. Dacă scanarea adaugă piese în timpul
analizei, jobul le ia și pe ele înainte să se termine.
"""

import logging
import threading
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from mixmatch.analysis.track import AnalysisResult, analyze_file
from mixmatch.config import settings
from mixmatch.db.models import JobKind, Track, Waveform, utcnow
from mixmatch.jobs import JobQueue

log = logging.getLogger(__name__)

_start_lock = threading.Lock()
# Dacă un job de analiză rulează în acest proces. Starea din `jobs` nu ajunge: un job care tocmai
# a decis să se oprească e încă „running” în bază câteva milisecunde.
_job_running = False


def _needs_analysis():  # type: ignore[no-untyped-def]
    return or_(Track.analysis_version.is_(None), Track.analysis_version < settings.analysis_version)


def pending_track_ids(session: Session) -> list[int]:
    return list(session.scalars(select(Track.id).where(_needs_analysis()).order_by(Track.id)))


def _save(session: Session, track_id: int, path: str, result: AnalysisResult) -> None:
    track = session.get(Track, track_id)
    # Piesa poate fi ștearsă de o rescanare în timpul analizei, iar SQLite refolosește id-urile:
    # rezultatul se salvează doar dacă rândul e tot pentru același fișier.
    if track is None or track.path != path:
        return
    track.bpm = result.bpm
    track.first_beat_s = result.first_beat_s
    track.key_camelot = result.key_camelot
    track.energy = result.energy
    track.loudness_lufs = result.loudness_lufs
    track.intro_bars = result.intro_bars
    track.outro_bars = result.outro_bars
    waveform = session.get(Waveform, track_id)
    if result.peaks is None:
        if waveform is not None:
            session.delete(waveform)
    else:
        if waveform is None:
            waveform = Waveform(track_id=track_id)
            session.add(waveform)
        waveform.preview = result.peaks.preview
        waveform.peaks = result.peaks.lo
        waveform.peaks_hi = result.peaks.hi
    # Și o analiză eșuată primește versiunea curentă, ca să nu se reia la nesfârșit.
    track.analysis_version = settings.analysis_version
    track.analyzed_at = utcnow()
    session.commit()


def analyze_pending(
    sessions: sessionmaker[Session],
    report: Callable[[float], None],
    workers: int = settings.analysis_workers,
) -> int:
    global _job_running
    done = 0
    try:
        with sessions() as session, ProcessPoolExecutor(max_workers=workers) as pool:
            while True:
                # Decizia de oprire se ia sub același lock ca pornirea unui job nou: o scanare
                # care se termină acum fie e văzută aici, fie pornește ea un job nou.
                with _start_lock:
                    ids = pending_track_ids(session)
                    if not ids:
                        _job_running = False
                        break
                rows = session.execute(select(Track.id, Track.path).where(Track.id.in_(ids))).all()
                futures = {pool.submit(analyze_file, Path(p)): (tid, p) for tid, p in rows}
                for future in as_completed(futures):
                    _save(session, *futures[future], future.result())
                    done += 1
                    remaining = len(futures) - sum(f.done() for f in futures)
                    report(done / (done + remaining))
    finally:
        with _start_lock:
            _job_running = False
    log.info("Analiză terminată: %s piese", done)
    return done


def start_analysis_if_needed(queue: JobQueue, sessions: sessionmaker[Session]) -> int | None:
    """Pornește un job de analiză dacă există piese de analizat și nu rulează deja unul.

    Dacă rulează unul, el ia și piesele noi înainte să se oprească (vezi `analyze_pending`).
    """
    global _job_running
    with _start_lock, sessions() as session:
        if _job_running or not pending_track_ids(session):
            return None
        _job_running = True
        job_id, _ = queue.submit(JobKind.analysis, lambda report: analyze_pending(sessions, report))
        return job_id
