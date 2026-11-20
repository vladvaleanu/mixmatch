import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile
from pydantic import BaseModel
from sqlalchemy import select

from mixmatch.analysis.runner import start_analysis_if_needed
from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.config import settings
from mixmatch.db.models import Job, JobKind, JobStatus, LibraryFolder
from mixmatch.db.session import SessionLocal
from mixmatch.jobs import Report, queue
from mixmatch.library.scan import scan_folder

router = APIRouter(tags=["library"])


class AddFolderIn(BaseModel):
    path: str


class AddFolderOut(BaseModel):
    folder_id: int
    job_id: int


@router.post(
    "/library/folders",
    status_code=202,
    operation_id="add_library_folder",
    responses=responses(400, 409),
)
def add_library_folder(body: AddFolderIn, session: SessionDep) -> AddFolderOut:
    """Adaugă un folder (sau îl rescanează, dacă există deja) și pornește scanarea.

    După scanare pornește automat analiza pieselor noi sau schimbate.
    """
    path = Path(body.path.strip()).expanduser()
    if not body.path.strip() or not path.is_dir():
        raise ApiError(400, "folder_not_found", f"Folderul nu există: {body.path}")
    path = path.resolve()

    folder_id, job_id = start_scan(session, path)
    return AddFolderOut(folder_id=folder_id, job_id=job_id)


def start_scan(session: SessionDep, path: Path) -> tuple[int, int]:
    """Înregistrează folderul (dacă e nou) și pornește scanarea, urmată de analiză.

    409 dacă o altă scanare e deja în curs.
    """
    busy = session.scalar(
        select(Job.id).where(
            Job.kind == JobKind.scan, Job.status.in_([JobStatus.queued, JobStatus.running])
        )
    )
    if busy is not None:
        raise ApiError(409, "scan_in_progress", "O scanare e deja în curs. Așteaptă să se termine.")

    folder = session.scalar(select(LibraryFolder).where(LibraryFolder.path == str(path)))
    if folder is None:
        folder = LibraryFolder(path=str(path))
        session.add(folder)
        session.commit()
    folder_id = folder.id

    def scan_then_analyze(report: Report) -> None:
        scan_folder(folder_id, SessionLocal, report)
        start_analysis_if_needed(queue, SessionLocal)

    job_id, _ = queue.submit(JobKind.scan, scan_then_analyze)
    return folder_id, job_id


class UploadOut(BaseModel):
    saved: list[str]  # numele fișierelor copiate în folderul administrat
    skipped: list[str]  # ce nu e audio (formatele acceptate: MP3, FLAC, WAV, AIFF, M4A)
    folder_id: int
    job_id: int  # scanarea folderului administrat


def _unique(folder: Path, name: str) -> Path:
    stem, suffix = Path(name).stem, Path(name).suffix
    candidate, n = folder / name, 2
    while candidate.exists():
        candidate, n = folder / f"{stem} ({n}){suffix}", n + 1
    return candidate


@router.post(
    "/library/upload", status_code=202, operation_id="upload_tracks", responses=responses(409)
)
def upload_tracks(files: list[UploadFile], session: SessionDep) -> UploadOut:
    """Copiază fișierele trase în Bibliotecă în folderul administrat, apoi îl scanează.

    Un fișier identic (același nume și aceeași mărime) deja copiat nu se copiază din nou.
    """
    busy = session.scalar(
        select(Job.id).where(
            Job.kind == JobKind.scan, Job.status.in_([JobStatus.queued, JobStatus.running])
        )
    )
    if busy is not None:
        raise ApiError(409, "scan_in_progress", "O scanare e deja în curs. Așteaptă să se termine.")
    folder = settings.uploads_dir
    folder.mkdir(parents=True, exist_ok=True)
    saved, skipped = [], []
    for upload in files:
        name = Path(upload.filename or "").name  # fără căi: nimic în afara folderului
        if not name or Path(name).suffix.lower() not in settings.audio_extensions:
            skipped.append(name or "?")
            continue
        size = upload.size
        existing = folder / name
        if existing.exists() and size is not None and existing.stat().st_size == size:
            saved.append(name)
            continue
        target = _unique(folder, name)
        with target.open("wb") as out:
            shutil.copyfileobj(upload.file, out)
        saved.append(target.name)
    folder_id, job_id = start_scan(session, folder.resolve())
    return UploadOut(saved=saved, skipped=skipped, folder_id=folder_id, job_id=job_id)
