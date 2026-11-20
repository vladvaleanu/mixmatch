from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mixmatch.db.models import Job, LibraryFolder, Mix, MixItem, Track, Waveform
from mixmatch.db.session import SessionLocal
from mixmatch.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        with SessionLocal.begin() as session:
            for model in (MixItem, Mix, Waveform, Track, LibraryFolder, Job):
                session.execute(delete(model))
        yield test_client


@pytest.fixture
def ids(client: TestClient) -> list[int]:
    with SessionLocal.begin() as session:
        tracks = [
            Track(path=f"/m/{i}.mp3", file_hash=str(i), title=f"Piesa {i}", duration_s=300 + i)
            for i in range(4)
        ]
        session.add_all(tracks)
        session.flush()
        return [t.id for t in tracks]


def test_create_and_list(client: TestClient, ids: list[int]) -> None:
    created = client.post("/api/mixes", json={"name": "  Set de vineri ", "track_ids": ids[:2]})
    assert created.status_code == 201
    mix = created.json()
    assert (mix["name"], mix["energy_shape"]) == ("Set de vineri", "free")
    assert [t["id"] for t in mix["tracks"]] == ids[:2]
    assert mix["duration_s"] == 601

    client.post("/api/mixes", json={})
    listed = client.get("/api/mixes").json()
    assert [(m["name"], m["track_count"]) for m in listed] == [("Mix nou", 0), ("Set de vineri", 2)]
    assert listed[1]["duration_s"] == 601


def test_order_is_saved(client: TestClient, ids: list[int]) -> None:
    mix_id = client.post("/api/mixes", json={"track_ids": ids}).json()["id"]
    new_order = [ids[2], ids[0], ids[3]]  # reordonare + scoatere

    saved = client.put(f"/api/mixes/{mix_id}/items", json={"track_ids": new_order}).json()

    assert [t["id"] for t in saved["tracks"]] == new_order
    # „Rămâne după refresh”: o cerere nouă citește aceeași ordine din bază.
    assert [t["id"] for t in client.get(f"/api/mixes/{mix_id}").json()["tracks"]] == new_order


def test_track_only_once_per_mix(client: TestClient, ids: list[int]) -> None:
    mix_id = client.post("/api/mixes", json={}).json()["id"]
    response = client.put(f"/api/mixes/{mix_id}/items", json={"track_ids": [ids[0], ids[0]]})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "duplicate_track"


def test_unknown_track_is_rejected(client: TestClient) -> None:
    mix_id = client.post("/api/mixes", json={}).json()["id"]
    response = client.put(f"/api/mixes/{mix_id}/items", json={"track_ids": [999999]})
    assert response.json()["error"]["code"] == "unknown_track"
    assert client.get(f"/api/mixes/{mix_id}").json()["tracks"] == []  # nimic salvat


def test_rename(client: TestClient) -> None:
    mix_id = client.post("/api/mixes", json={}).json()["id"]
    assert client.patch(f"/api/mixes/{mix_id}", json={"name": "Vârf"}).json()["name"] == "Vârf"
    blank = client.patch(f"/api/mixes/{mix_id}", json={"name": "   "})
    assert blank.status_code == 422


def test_delete(client: TestClient, ids: list[int]) -> None:
    mix_id = client.post("/api/mixes", json={"track_ids": ids}).json()["id"]
    assert client.delete(f"/api/mixes/{mix_id}").status_code == 204
    assert client.get(f"/api/mixes/{mix_id}").json()["error"]["code"] == "mix_not_found"
    with SessionLocal() as session:
        assert session.scalars(select(MixItem)).all() == []
        assert len(session.scalars(select(Track)).all()) == 4  # piesele rămân în bibliotecă


def test_deleted_track_leaves_the_mix(client: TestClient, ids: list[int]) -> None:
    mix_id = client.post("/api/mixes", json={"track_ids": ids[:3]}).json()["id"]
    with SessionLocal.begin() as session:
        session.delete(session.get(Track, ids[1]))  # ca la o rescanare
    remaining = client.get(f"/api/mixes/{mix_id}").json()["tracks"]
    assert [t["id"] for t in remaining] == [ids[0], ids[2]]


def test_editing_items_moves_mix_to_top(client: TestClient, ids: list[int]) -> None:
    old = client.post("/api/mixes", json={"name": "Vechi"}).json()["id"]
    client.post("/api/mixes", json={"name": "Nou"})
    client.put(f"/api/mixes/{old}/items", json={"track_ids": ids[:1]})
    assert client.get("/api/mixes").json()[0]["name"] == "Vechi"


def test_unknown_mix_is_404(client: TestClient) -> None:
    response = client.put("/api/mixes/999999/items", json={"track_ids": []})
    assert response.json()["error"]["code"] == "mix_not_found"
