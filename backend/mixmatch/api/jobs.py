from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

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


def _out(job: Job) -> JobOut:
    return JobOut(
        id=job.id, kind=job.kind, status=job.status, progress=job.progress, error=job.error
    )


# Declarată înaintea lui /jobs/{job_id}, ca „active” să nu fie citit ca id.
@router.get("/jobs/active", operation_id="list_active_jobs")
def list_active_jobs(session: SessionDep) -> list[JobOut]:
    """Joburile în așteptare sau în lucru (ex. analiza pornită după o scanare)."""
    jobs = session.scalars(
        select(Job).where(Job.status.in_([JobStatus.queued, JobStatus.running])).order_by(Job.id)
    )
    return [_out(job) for job in jobs]


@router.get("/jobs/{job_id}", operation_id="get_job", responses=responses(404))
def get_job(job_id: int, session: SessionDep) -> JobOut:
    job = session.get(Job, job_id)
    if job is None:
        raise ApiError(404, "job_not_found", f"Jobul {job_id} nu există")
    return _out(job)
