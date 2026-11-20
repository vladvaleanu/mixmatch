import time
from pathlib import Path

from fastapi.testclient import TestClient

from mixmatch.config import settings
from tests.audio import make_audio


def wait(client: TestClient, job_id: int) -> None:
    deadline = time.monotonic() + 30
    while client.get(f"/api/jobs/{job_id}").json()["status"] not in ("done", "failed"):
        assert time.monotonic() < deadline
        time.sleep(0.05)


def files(*paths: tuple[str, Path]) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        ("files", (name, path.read_bytes(), "application/octet-stream")) for name, path in paths
    ]


def test_upload_copies_audio_and_scans(client: TestClient, tmp_path: Path) -> None:
    for old in settings.uploads_dir.glob("*"):
        old.unlink()
    a = make_audio(tmp_path / "a.mp3", duration_s=61, title="Alfa")
    b = make_audio(tmp_path / "b.flac", duration_s=61, title="Beta")
    note = tmp_path / "note.txt"
    note.write_text("nu e audio")

    out = client.post(
        "/api/library/upload", files=files(("a.mp3", a), ("b.flac", b), ("note.txt", note))
    )
    assert out.status_code == 202
    body = out.json()
    assert (sorted(body["saved"]), body["skipped"]) == (["a.mp3", "b.flac"], ["note.txt"])
    wait(client, body["job_id"])
    assert sorted(t["title"] for t in client.get("/api/tracks").json()) == ["Alfa", "Beta"]
    assert (settings.uploads_dir / "a.mp3").read_bytes() == a.read_bytes()

    # Același fișier din nou: nu se dublează.
    again = client.post("/api/library/upload", files=files(("a.mp3", a))).json()
    wait(client, again["job_id"])
    assert len(client.get("/api/tracks").json()) == 2

    # Alt conținut cu același nume: primește un nume nou.
    other = make_audio(tmp_path / "x.mp3", duration_s=62, title="Alta")
    renamed = client.post("/api/library/upload", files=files(("a.mp3", other))).json()
    assert renamed["saved"] == ["a (2).mp3"]
    wait(client, renamed["job_id"])


def test_upload_cannot_escape_the_folder(client: TestClient, tmp_path: Path) -> None:
    a = make_audio(tmp_path / "a.mp3", duration_s=61)
    body = client.post("/api/library/upload", files=files(("../../evil.mp3", a))).json()
    assert body["saved"] == ["evil.mp3"]
    assert (settings.uploads_dir / "evil.mp3").is_file()
    wait(client, body["job_id"])
