import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from mixmatch.db.models import Job, LibraryFolder, Track
from mixmatch.db.session import SessionLocal
from mixmatch.main import app
from tests.audio import make_audio


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:  # pornește lifespan-ul: migrări pe baza de test
        with SessionLocal.begin() as session:
            for model in (Track, LibraryFolder, Job):
                session.execute(delete(model))
        yield test_client


def wait_for_job(client: TestClient, job_id: int) -> dict[str, object]:
    deadline = time.monotonic() + 10
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
