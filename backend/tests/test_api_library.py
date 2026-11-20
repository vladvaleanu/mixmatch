import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mixmatch.db.models import Track
from mixmatch.db.session import SessionLocal
from tests.audio import make_audio, make_music


def wait_for_job(client: TestClient, job_id: int) -> dict[str, object]:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("done", "failed"):
            return job
        time.sleep(0.05)
    raise AssertionError(f"Jobul {job_id} nu s-a terminat")


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    make_audio(tmp_path / "b.mp3", duration_s=61, title="Beta", artist="X")
    make_audio(tmp_path / "a.flac", duration_s=61, title="alfa", artist="Y")
    make_audio(tmp_path / "sample.wav", duration_s=1)
    return tmp_path


def test_add_folder_scans_and_lists_tracks(client: TestClient, folder: Path) -> None:
    response = client.post("/api/library/folders", json={"path": str(folder)})
    assert response.status_code == 202
    job = wait_for_job(client, response.json()["job_id"])
    assert (job["kind"], job["status"], job["progress"]) == ("scan", "done", 1.0)

    listed = client.get("/api/tracks").json()
    assert [(t["title"], t["artist"]) for t in listed] == [("alfa", "Y"), ("Beta", "X")]
    assert listed[0]["duration_s"] == pytest.approx(61, abs=0.2)


def test_scan_starts_analysis(client: TestClient, tmp_path: Path) -> None:
    make_music(tmp_path / "song.wav", bpm=124, root_hz=220.0, minor=True, duration_s=61)
    scan = client.post("/api/library/folders", json={"path": str(tmp_path)}).json()
    wait_for_job(client, scan["job_id"])

    active = client.get("/api/jobs/active").json()
    analysis = [job for job in active if job["kind"] == "analysis"]
    if analysis:  # poate s-a terminat deja
        assert wait_for_job(client, analysis[0]["id"])["status"] == "done"
    deadline = time.monotonic() + 20
    while not (track := client.get("/api/tracks").json()[0])["analyzed"]:
        assert time.monotonic() < deadline, "Analiza nu s-a terminat"
        time.sleep(0.1)

    assert track["bpm"] == pytest.approx(124, abs=1)
    assert (track["key_camelot"], track["key_name"]) == ("8A", "La minor")
    assert client.get("/api/jobs/active").json() == []
    assert track["energy"] in range(1, 6)
    assert len(track["waveform_preview"]) == 40


def test_manual_energy_overrides_and_resets(client: TestClient) -> None:
    with SessionLocal.begin() as session:
        track = Track(path="/x.mp3", file_hash="h", title="X", duration_s=300, energy=2)
        session.add(track)
        session.flush()
        track_id = track.id

    corrected = client.patch(f"/api/tracks/{track_id}", json={"energy_manual": 5}).json()
    assert (corrected["energy"], corrected["energy_manual"]) == (5, 5)
    assert client.get("/api/tracks").json()[0]["energy"] == 5

    reset = client.patch(f"/api/tracks/{track_id}", json={"energy_manual": None}).json()
    assert (reset["energy"], reset["energy_manual"]) == (2, None)


@pytest.mark.parametrize("value", [0, 6, "mare"])
def test_manual_energy_must_be_1_to_5(client: TestClient, value: object) -> None:
    with SessionLocal.begin() as session:
        session.add(Track(path="/y.mp3", file_hash="h", title="Y", duration_s=300))
    track_id = client.get("/api/tracks").json()[0]["id"]
    response = client.patch(f"/api/tracks/{track_id}", json={"energy_manual": value})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_patch_unknown_track_is_404(client: TestClient) -> None:
    response = client.patch("/api/tracks/999999", json={"energy_manual": 3})
    assert response.json()["error"]["code"] == "track_not_found"


def test_adding_same_folder_twice_rescans_without_duplicates(
    client: TestClient, folder: Path
) -> None:
    first = client.post("/api/library/folders", json={"path": str(folder)}).json()
    wait_for_job(client, first["job_id"])
    second = client.post("/api/library/folders", json={"path": f"{folder}/"}).json()
    wait_for_job(client, second["job_id"])

    assert second["folder_id"] == first["folder_id"]
    assert len(client.get("/api/tracks").json()) == 2


def test_missing_folder_is_an_error(client: TestClient, tmp_path: Path) -> None:
    response = client.post("/api/library/folders", json={"path": str(tmp_path / "nu-exista")})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "folder_not_found"


def test_invalid_body_uses_error_shape(client: TestClient) -> None:
    response = client.post("/api/library/folders", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_unknown_job_is_404(client: TestClient) -> None:
    response = client.get("/api/jobs/999999")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "job_not_found", "message": "Jobul 999999 nu există"}
    }


def test_unknown_route_uses_error_shape(client: TestClient) -> None:
    response = client.get("/api/nu-exista")
    assert response.json()["error"]["code"] == "not_found"
