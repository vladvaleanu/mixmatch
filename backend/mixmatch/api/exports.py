import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select

from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.api.jobs import JobOut, job_out
from mixmatch.api.mixes import load_mix
from mixmatch.config import settings
from mixmatch.db.models import Export, Job, JobKind
from mixmatch.db.session import SessionLocal
from mixmatch.export.render import MixTrack, render_mix
from mixmatch.export.tracklist import Entry, cue_sheet, tracklist
from mixmatch.jobs import Report, queue
from mixmatch.mixes.plans import plan_for

router = APIRouter(tags=["exports"])

_UNSAFE = re.compile(r'[/\\:*?"<>|\x00-\x1f]+')


class ExportIn(BaseModel):
    format: Literal["wav", "mp3"] = "wav"


class ExportStarted(BaseModel):
    export_id: int
    job_id: int
    path: str  # unde va fi fișierul când jobul se termină


FileKind = Literal["audio", "tracklist", "cue"]


class ExportOut(BaseModel):
    id: int
    mix_id: int | None  # None dacă mixul a fost șters între timp
    mix_name: str
    format: str
    path: str
    duration_s: float | None  # cunoscută după randare
    created_at: datetime
    job: JobOut | None
    files: list[FileKind]  # ce fișiere există acum pe disc


def files_of(audio: Path) -> dict[FileKind, Path]:
    """Fișierele unui export: audio, tracklistul (.txt) și .cue, cu același nume."""
    return {
        "audio": audio,
        "tracklist": audio.with_suffix(".txt"),
        "cue": audio.with_suffix(".cue"),
    }


def safe_name(name: str) -> str:
    """Un nume de fișier valid pe macOS și Windows, din numele mixului."""
    cleaned = _UNSAFE.sub("-", name).strip(" .-")
    return cleaned or "mix"


def output_path(mix_name: str, fmt: str) -> Path:
    """`<exports>/<mix>/<mix>.<fmt>`; dacă există deja: „<mix> (2)”, „<mix> (3)”…"""
    name = safe_name(mix_name)
    folder = settings.exports_dir / name
    candidate, n = folder / f"{name}.{fmt}", 2
    while candidate.exists():
        candidate, n = folder / f"{name} ({n}).{fmt}", n + 1
    return candidate


@router.post(
    "/mixes/{mix_id}/export",
    status_code=202,
    operation_id="export_mix",
    responses=responses(404, 409, 422),
)
def export_mix(mix_id: int, body: ExportIn, session: SessionDep) -> ExportStarted:
    """Pornește randarea mixului (WAV 16-bit/44,1 kHz sau MP3 320 kbps) ca job."""
    mix = load_mix(session, mix_id)
    tracks = [item.track for item in mix.items]
    if not tracks:
        raise ApiError(409, "empty_mix", "Mixul e gol: adaugă piese înainte de export.")
    plans = []
    for a, b in zip(tracks, tracks[1:], strict=False):
        plan = plan_for(session, mix, a, b)
        if plan is None:
            raise ApiError(
                409, "not_analyzed", "Exportul se poate face după analiza tuturor pieselor."
            )
        plans.append(plan)
    items = [
        MixTrack(title=t.title, path=Path(t.path), loudness_lufs=t.loudness_lufs) for t in tracks
    ]
    meta = [(t.title, t.artist) for t in tracks]
    path = output_path(mix.name, body.format)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()  # rezervă numele: un al doilea export nu-l va alege pe același
    export = Export(mix_id=mix.id, mix_name=mix.name, format=body.format, path=str(path))
    session.add(export)
    session.commit()
    export_id, mix_name, fmt = export.id, mix.name, body.format

    def render(report: Report) -> None:
        try:
            result = render_mix(items, plans, path, fmt, report)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        entries = [
            Entry(title=title, artist=artist, start_s=start)
            for (title, artist), start in zip(meta, result.track_starts_s, strict=True)
        ]
        files = files_of(path)
        files["tracklist"].write_text(tracklist(mix_name, entries), encoding="utf-8")
        files["cue"].write_text(cue_sheet(mix_name, path.name, fmt, entries), encoding="utf-8")
        with SessionLocal.begin() as job_session:
            row = job_session.get(Export, export_id)
            if row is not None:
                row.duration_s = round(result.duration_s, 3)

    job_id, _ = queue.submit(JobKind.export, render)
    with SessionLocal.begin() as link:
        row = link.get(Export, export_id)
        if row is not None:
            row.job_id = job_id
    return ExportStarted(export_id=export_id, job_id=job_id, path=str(path))


@router.get("/exports", operation_id="list_exports")
def list_exports(session: SessionDep) -> list[ExportOut]:
    """Exporturile, cele mai noi primele, cu starea jobului și fișierele existente."""
    rows = session.execute(
        select(Export, Job).outerjoin(Job, Job.id == Export.job_id).order_by(Export.id.desc())
    )
    out = []
    for export, job in rows:
        files = files_of(Path(export.path))
        out.append(
            ExportOut(
                id=export.id,
                mix_id=export.mix_id,
                mix_name=export.mix_name,
                format=export.format,
                path=export.path,
                duration_s=export.duration_s,
                created_at=export.created_at,
                job=job_out(job) if job else None,
                files=[
                    kind
                    for kind, p in files.items()
                    if p.is_file() and (kind != "audio" or p.stat().st_size > 0)
                ],
            )
        )
    return out


@router.get(
    "/exports/{export_id}/file",
    operation_id="get_export_file",
    response_class=FileResponse,
    responses={**responses(404), 200: {"content": {"application/octet-stream": {}}}},
)
def get_export_file(export_id: int, session: SessionDep, kind: FileKind = "audio") -> FileResponse:
    """Descarcă fișierul audio, tracklistul sau .cue al unui export."""
    export = session.get(Export, export_id)
    if export is None:
        raise ApiError(404, "export_not_found", f"Exportul {export_id} nu există")
    path = files_of(Path(export.path))[kind]
    if not path.is_file() or path.stat().st_size == 0:
        raise ApiError(404, "file_missing", f"Fișierul nu există (încă): {path.name}")
    return FileResponse(path, filename=path.name)
