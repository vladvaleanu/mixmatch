from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from mixmatch.analysis.runner import start_analysis_if_needed
from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
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
    return AddFolderOut(folder_id=folder_id, job_id=job_id)
