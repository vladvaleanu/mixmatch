from fastapi import APIRouter
from pydantic import BaseModel

from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.db.models import Job, JobKind, JobStatus

router = APIRouter(tags=["jobs"])


class JobOut(BaseModel):
    id: int
    kind: JobKind
    status: JobStatus
    progress: float
    error: str | None


@router.get("/jobs/{job_id}", operation_id="get_job", responses=responses(404))
def get_job(job_id: int, session: SessionDep) -> JobOut:
    job = session.get(Job, job_id)
    if job is None:
        raise ApiError(404, "job_not_found", f"Jobul {job_id} nu există")
    return JobOut(
        id=job.id, kind=job.kind, status=job.status, progress=job.progress, error=job.error
    )
