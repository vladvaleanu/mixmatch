from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from mixmatch.db.models import Track
from mixmatch.db.session import SessionLocal


@pytest.fixture
def ids(client: TestClient) -> list[int]:
    now = datetime.now(UTC)
    with SessionLocal.begin() as session:
        tracks = [
            Track(
                path=f"/c/{i}",
                file_hash=f"c{i}",
                title=t,
                duration_s=300,
                added_at=now - timedelta(days=d),
            )  # fmt: skip
            for i, (t, d) in enumerate((("Veche", 30), ("Nouă", 0), ("Mijlocie", 7)))
        ]
        session.add_all(tracks)
        session.flush()
        return [t.id for t in tracks]


def titles(client: TestClient, query: str = "") -> list[str]:
    return [t["title"] for t in client.get(f"/api/tracks{query}").json()]


def test_collections_crud_and_membership(client: TestClient, ids: list[int]) -> None:
    warm = client.post("/api/collections", json={"name": "  Încălzire "}).json()
    peak = client.post("/api/collections", json={"name": "Vârf de seară"}).json()
    assert warm["name"] == "Încălzire"
    assert client.post("/api/collections", json={"name": "Încălzire"}).status_code == 409

    client.put(f"/api/collections/{warm['id']}/tracks/{ids[0]}")
    added = client.put(f"/api/collections/{warm['id']}/tracks/{ids[2]}").json()
    client.put(f"/api/collections/{warm['id']}/tracks/{ids[2]}")  # de două ori: fără dublură
    client.put(f"/api/collections/{peak['id']}/tracks/{ids[2]}")
    assert added["track_count"] == 2
    assert [(c["name"], c["track_count"]) for c in client.get("/api/collections").json()] == [
        ("Încălzire", 2),
        ("Vârf de seară", 1),
    ]
    assert titles(client, f"?collection={warm['id']}") == ["Mijlocie", "Veche"]
    by_title = {t["title"]: t for t in client.get("/api/tracks").json()}
    assert sorted(by_title["Mijlocie"]["collection_ids"]) == sorted([warm["id"], peak["id"]])

    # Corectura energiei nu „pierde” colecțiile din răspuns.
    patched = client.patch(f"/api/tracks/{ids[2]}", json={"energy_manual": 3}).json()
    assert sorted(patched["collection_ids"]) == sorted([warm["id"], peak["id"]])

    client.delete(f"/api/collections/{warm['id']}/tracks/{ids[0]}")
    assert titles(client, f"?collection={warm['id']}") == ["Mijlocie"]

    renamed = client.patch(f"/api/collections/{peak['id']}", json={"name": "Vârf"}).json()
    assert renamed["name"] == "Vârf"
    assert client.delete(f"/api/collections/{warm['id']}").status_code == 204
    assert len(titles(client)) == 3  # piesele rămân
    assert client.get("/api/tracks").json()[0]["collection_ids"] in ([], [peak["id"]])


def test_recently_added_first(client: TestClient, ids: list[int]) -> None:
    assert titles(client, "?sort=recent") == ["Nouă", "Mijlocie", "Veche"]


def test_errors(client: TestClient, ids: list[int]) -> None:
    assert (
        client.put(f"/api/collections/999/tracks/{ids[0]}").json()["error"]["code"]
        == "collection_not_found"
    )
    c = client.post("/api/collections", json={"name": "X"}).json()
    assert (
        client.put(f"/api/collections/{c['id']}/tracks/999999").json()["error"]["code"]
        == "track_not_found"
    )
    assert client.post("/api/collections", json={"name": "   "}).status_code == 422
