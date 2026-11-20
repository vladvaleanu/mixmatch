import re
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.api.mixes import load_mix
from mixmatch.config import settings
from mixmatch.db.models import JobKind
from mixmatch.export.render import MixTrack, render_mix
from mixmatch.jobs import Report, queue
from mixmatch.mixes.plans import plan_for

router = APIRouter(tags=["exports"])

_UNSAFE = re.compile(r'[/\\:*?"<>|\x00-\x1f]+')


class ExportIn(BaseModel):
    format: Literal["wav", "mp3"] = "wav"


class ExportStarted(BaseModel):
    job_id: int
    path: str  # unde va fi fișierul când jobul se termină


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
    path = output_path(mix.name, body.format)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()  # rezervă numele: un al doilea export nu-l va alege pe același

    def render(report: Report) -> None:
        try:
            render_mix(items, plans, path, body.format, report)
        except Exception:
            path.unlink(missing_ok=True)
            raise

    job_id, _ = queue.submit(JobKind.export, render)
    return ExportStarted(job_id=job_id, path=str(path))
