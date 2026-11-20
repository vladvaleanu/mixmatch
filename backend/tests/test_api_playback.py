from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from mixmatch.config import settings
from mixmatch.db.models import Job, LibraryFolder, Mix, MixItem, Track, Waveform
from mixmatch.db.session import SessionLocal
from mixmatch.main import app
from tests.audio import make_audio


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        with SessionLocal.begin() as session:
            for model in (MixItem, Mix, Waveform, Track, LibraryFolder, Job):
                session.execute(delete(model))
        yield test_client


def add_track(path: Path, file_hash: str = "hash", waveform: bool = False) -> int:
    with SessionLocal.begin() as session:
        track = Track(path=str(path), file_hash=file_hash, title=path.stem, duration_s=2)
        session.add(track)
        session.flush()
        if waveform:
            session.add(
                Waveform(
                    track_id=track.id,
                    preview=bytes(40),
                    peaks=bytes(range(250)) * 4,
                    peaks_hi=bytes(8000),
                )
            )
        return track.id


def test_audio_supports_range(client: TestClient, tmp_path: Path) -> None:
    song = make_audio(tmp_path / "a.mp3")
    track_id = add_track(song)

    full = client.get(f"/api/tracks/{track_id}/audio")
    assert full.status_code == 200
    assert full.headers["content-type"] == "audio/mpeg"
    assert full.headers["accept-ranges"] == "bytes"
    assert full.content == song.read_bytes()

    part = client.get(f"/api/tracks/{track_id}/audio", headers={"Range": "bytes=100-199"})
    assert part.status_code == 206
    assert part.headers["content-range"] == f"bytes 100-199/{song.stat().st_size}"
    assert part.content == song.read_bytes()[100:200]


@pytest.mark.parametrize(("ext", "media_type"), [("flac", "audio/flac"), ("m4a", "audio/mp4")])
def test_audio_media_types(client: TestClient, tmp_path: Path, ext: str, media_type: str) -> None:
    track_id = add_track(make_audio(tmp_path / f"a.{ext}"))
    assert client.get(f"/api/tracks/{track_id}/audio").headers["content-type"] == media_type


def test_aiff_is_served_as_cached_flac(client: TestClient, tmp_path: Path) -> None:
    track_id = add_track(make_audio(tmp_path / "a.aiff"), file_hash="aiffhash")
    cached = settings.cache_dir / "aiffhash.flac"
    cached.unlink(missing_ok=True)

    response = client.get(f"/api/tracks/{track_id}/audio")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/flac"
    assert response.content[:4] == b"fLaC"
    assert cached.is_file()
    assert client.get(f"/api/tracks/{track_id}/audio").content == response.content  # din cache


def test_missing_file_is_404(client: TestClient, tmp_path: Path) -> None:
    track_id = add_track(tmp_path / "dispărut.mp3")
    response = client.get(f"/api/tracks/{track_id}/audio")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "file_missing"


def test_unknown_track_audio_is_404(client: TestClient) -> None:
    assert client.get("/api/tracks/999999/audio").json()["error"]["code"] == "track_not_found"


def test_waveform_resolutions(client: TestClient, tmp_path: Path) -> None:
    track_id = add_track(tmp_path / "a.mp3", waveform=True)
    lo = client.get(f"/api/tracks/{track_id}/waveform").json()["peaks"]
    hi = client.get(f"/api/tracks/{track_id}/waveform?res=hi").json()["peaks"]
    assert (len(lo), len(hi)) == (1000, 8000)
    assert lo[:3] == [0, 1, 2]


def test_waveform_before_analysis_is_404(client: TestClient, tmp_path: Path) -> None:
    track_id = add_track(tmp_path / "a.mp3")
    response = client.get(f"/api/tracks/{track_id}/waveform")
    assert response.json()["error"]["code"] == "waveform_not_ready"


def test_waveform_rejects_unknown_resolution(client: TestClient, tmp_path: Path) -> None:
    track_id = add_track(tmp_path / "a.mp3", waveform=True)
    assert client.get(f"/api/tracks/{track_id}/waveform?res=max").status_code == 422
