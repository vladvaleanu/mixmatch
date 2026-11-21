from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from mixmatch.api.errors import install_error_handlers
from mixmatch.main import mount_frontend


def make_client(dist: Path) -> TestClient:
    app = FastAPI()
    install_error_handlers(app)
    api = APIRouter()

    @api.get("/ping")
    def ping() -> dict[str, str]:
        return {"pong": "ok"}

    app.include_router(api, prefix="/api")
    mount_frontend(app, dist)
    return TestClient(app)


def make_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>mixmatch</html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("nu")
    return dist


def test_serves_index_and_assets(tmp_path: Path) -> None:
    client = make_client(make_dist(tmp_path))
    root = client.get("/")
    assert root.status_code == 200
    assert "mixmatch" in root.text
    assert root.headers["cache-control"] == "no-cache"
    asset = client.get("/assets/app.js")
    assert asset.status_code == 200
    assert asset.text == "console.log(1)"


def test_browser_routes_get_index(tmp_path: Path) -> None:
    client = make_client(make_dist(tmp_path))
    response = client.get("/mixes/3")
    assert response.status_code == 200
    assert "mixmatch" in response.text


def test_api_routes_win_and_unknown_api_stays_json_404(tmp_path: Path) -> None:
    client = make_client(make_dist(tmp_path))
    assert client.get("/api/ping").json() == {"pong": "ok"}
    missing = client.get("/api/nu-exista")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_no_files_outside_dist(tmp_path: Path) -> None:
    client = make_client(make_dist(tmp_path))
    response = client.get("/..%2Fsecret.txt")
    assert response.text != "nu"
    assert "mixmatch" in response.text


def test_nothing_mounted_without_build(tmp_path: Path) -> None:
    client = make_client(tmp_path / "lipsa")
    assert client.get("/").status_code == 404
    assert client.get("/api/ping").status_code == 200
