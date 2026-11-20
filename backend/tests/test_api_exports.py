import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mixmatch.api.exports import output_path, safe_name
from mixmatch.config import settings
from mixmatch.db.models import Track
from mixmatch.db.session import SessionLocal
from tests.audio import make_music


@pytest.fixture
def mix_id(client: TestClient, tmp_path: Path) -> int:
    ids = []
    with SessionLocal.begin() as session:
        for i, bpm in enumerate((124.0, 125.0)):
            path = make_music(tmp_path / f"{i}.wav", bpm, 220.0, True, duration_s=40)
            track = Track(path=str(path), file_hash=f"e{i}", title=f"Piesa {i}", duration_s=40.0,
                          bpm=bpm, key_camelot="8A", energy=3, first_beat_s=0.5,
                          analysis_version=settings.analysis_version)  # fmt: skip
            session.add(track)
            session.flush()
            ids.append(track.id)
    return client.post("/api/mixes", json={"name": "Set: test/1", "track_ids": ids}).json()["id"]


def wait(client: TestClient, job_id: int) -> dict[str, object]:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("done", "failed"):
            return job
        time.sleep(0.05)
    raise AssertionError("exportul nu s-a terminat")


@pytest.mark.parametrize("fmt", ["wav", "mp3"])
def test_export_writes_the_file(client: TestClient, mix_id: int, fmt: str) -> None:
    client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"length_bars": 8})
    started = client.post(f"/api/mixes/{mix_id}/export", json={"format": fmt}).json()
    path = Path(started["path"])
    assert path.parent == settings.exports_dir / "Set- test-1"
    assert path.name == f"Set- test-1.{fmt}"
    job = wait(client, started["job_id"])
    assert job["status"] == "done", job["error"]
    assert path.stat().st_size > 100_000


def test_second_export_gets_a_new_name(client: TestClient, mix_id: int) -> None:
    first = client.post(f"/api/mixes/{mix_id}/export", json={"format": "wav"}).json()
    second = client.post(f"/api/mixes/{mix_id}/export", json={"format": "wav"}).json()
    assert second["path"] != first["path"]
    assert Path(second["path"]).name.startswith("Set- test-1 (")
    wait(client, first["job_id"])
    wait(client, second["job_id"])


def test_cannot_export_empty_or_unanalyzed(client: TestClient, tmp_path: Path) -> None:
    empty = client.post("/api/mixes", json={}).json()["id"]
    assert client.post(f"/api/mixes/{empty}/export", json={}).json()["error"]["code"] == "empty_mix"
    with SessionLocal.begin() as session:
        a = Track(path="/x/a.mp3", file_hash="ua", title="A", duration_s=300, bpm=124.0,
                  first_beat_s=0.5, analysis_version=settings.analysis_version)  # fmt: skip
        b = Track(path="/x/b.mp3", file_hash="ub", title="B", duration_s=300,
                  analysis_version=settings.analysis_version)  # fmt: skip
        session.add_all([a, b])
        session.flush()
        ids = [a.id, b.id]
    mix = client.post("/api/mixes", json={"track_ids": ids}).json()["id"]
    assert (
        client.post(f"/api/mixes/{mix}/export", json={}).json()["error"]["code"] == "not_analyzed"
    )


def test_names() -> None:
    assert safe_name("A/B: test?") == "A-B- test"
    assert safe_name("...") == "mix"
    assert output_path("Nou", "mp3").name == "Nou.mp3"


def test_export_list_tracklist_cue_and_download(client: TestClient, mix_id: int) -> None:
    client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"length_bars": 8})
    started = client.post(f"/api/mixes/{mix_id}/export", json={"format": "wav"}).json()
    listed = client.get("/api/exports").json()
    assert listed[0]["id"] == started["export_id"]
    assert listed[0]["job"]["kind"] == "export"
    wait(client, started["job_id"])

    item = client.get("/api/exports").json()[0]
    assert (item["mix_name"], item["format"]) == ("Set: test/1", "wav")
    assert item["files"] == ["audio", "tracklist", "cue"]
    assert item["duration_s"] > 40
    assert item["job"]["status"] == "done"

    text = client.get(f"/api/exports/{item['id']}/file?kind=tracklist").text
    assert text.splitlines()[2] == "01. [0:00] Piesa 0"
    assert text.splitlines()[3].endswith("] Piesa 1")
    cue = client.get(f"/api/exports/{item['id']}/file?kind=cue")
    assert 'FILE "Set- test-1' in cue.text
    audio = client.get(f"/api/exports/{item['id']}/file")
    assert audio.headers["content-disposition"].startswith("attachment;")
    assert audio.content[:4] == b"RIFF"


def test_export_survives_mix_deletion(client: TestClient, mix_id: int) -> None:
    started = client.post(f"/api/mixes/{mix_id}/export", json={"format": "mp3"}).json()
    wait(client, started["job_id"])
    client.delete(f"/api/mixes/{mix_id}")
    item = client.get("/api/exports").json()[0]
    assert (item["mix_id"], item["mix_name"]) == (None, "Set: test/1")


def test_missing_export_or_file(client: TestClient) -> None:
    assert client.get("/api/exports/999999/file").json()["error"]["code"] == "export_not_found"
    assert client.get("/api/exports/1/file?kind=pdf").status_code in (404, 422)
