from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from mixmatch.db.models import Job, LibraryFolder, Mix, MixItem, Track, Waveform
from mixmatch.db.session import SessionLocal
from mixmatch.main import app

LIBRARY = [
    # titlu, artist, bpm, ton, energie, energie manuală, durată
    ("Paper Lights", "Oda Kray", 124.0, "8A", 3, None, 348),
    ("Slow Orbit", "Mira Vey", 123.0, "9A", 3, None, 422),
    ("Neon Tide", "Lumen Field", 122.0, "8B", 2, 4, 372),
    ("Low Sun", "Haldor", 126.0, "3B", 5, None, 390),
    ("Rift", "Kaya Moll", 140.0, "8A", 5, None, 321),
    ("Necunoscută", None, None, None, None, None, 200),
]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        with SessionLocal.begin() as session:
            for model in (MixItem, Mix, Waveform, Track, LibraryFolder, Job):
                session.execute(delete(model))
            for i, (title, artist, bpm, key, energy, manual, duration) in enumerate(LIBRARY):
                session.add(
                    Track(
                        path=f"/m/{i}.mp3",
                        file_hash=str(i),
                        title=title,
                        artist=artist,
                        bpm=bpm,
                        key_camelot=key,
                        energy=energy,
                        energy_manual=manual,
                        duration_s=duration,
                    )
                )
        yield test_client


def titles(client: TestClient, query: str = "") -> list[str]:
    response = client.get(f"/api/tracks{query}")
    assert response.status_code == 200, response.text
    return [t["title"] for t in response.json()]


def track_id(client: TestClient, title: str) -> int:
    return next(t["id"] for t in client.get("/api/tracks").json() if t["title"] == title)


def test_search_title_and_artist(client: TestClient) -> None:
    assert titles(client, "?q=orbit") == ["Slow Orbit"]
    assert titles(client, "?q=haldor") == ["Low Sun"]


def test_bpm_range(client: TestClient) -> None:
    assert titles(client, "?bpm_min=123&bpm_max=126") == ["Low Sun", "Paper Lights", "Slow Orbit"]


def test_energy_uses_manual_correction(client: TestClient) -> None:
    assert titles(client, "?energy=4&energy=5") == ["Low Sun", "Neon Tide", "Rift"]


def test_keys(client: TestClient) -> None:
    assert titles(client, "?key=8A&key=8B") == ["Neon Tide", "Paper Lights", "Rift"]


def test_bad_key_is_rejected(client: TestClient) -> None:
    response = client.get("/api/tracks?key=13A")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


@pytest.mark.parametrize(
    ("sort", "expected"),
    [
        ("bpm", ["Neon Tide", "Slow Orbit", "Paper Lights", "Low Sun", "Rift", "Necunoscută"]),
        ("key", ["Low Sun", "Paper Lights", "Rift", "Neon Tide", "Slow Orbit", "Necunoscută"]),
        ("energy", ["Paper Lights", "Slow Orbit", "Neon Tide", "Low Sun", "Rift", "Necunoscută"]),
        ("duration", ["Necunoscută", "Rift", "Paper Lights", "Neon Tide", "Low Sun", "Slow Orbit"]),
    ],
)
def test_sort(client: TestClient, sort: str, expected: list[str]) -> None:
    assert titles(client, f"?sort={sort}") == expected


def test_compatible_with(client: TestClient) -> None:
    paper = track_id(client, "Paper Lights")
    # Slow Orbit (9A, −1 BPM) și Neon Tide (8B; energie 3 → 4) merg; Rift e la +13 %, Low Sun 3B.
    assert titles(client, f"?compatible_with={paper}") == ["Neon Tide", "Slow Orbit"]


def test_filters_combine(client: TestClient) -> None:
    paper = track_id(client, "Paper Lights")
    assert titles(client, f"?compatible_with={paper}&key=9A") == ["Slow Orbit"]


def test_matches_best_first_with_reason(client: TestClient) -> None:
    paper = track_id(client, "Paper Lights")
    matches = client.get(f"/api/tracks/{paper}/matches").json()
    assert [(m["track"]["title"], m["label"]) for m in matches] == [
        ("Slow Orbit", "smooth"),
        ("Neon Tide", "smooth"),
    ]
    assert matches[0]["reason"] == "8A → 9A · −1 BPM"
    assert matches[0]["score"] >= matches[1]["score"]


def test_matches_put_smooth_first_and_skip_duplicate_files(client: TestClient) -> None:
    with SessionLocal.begin() as session:
        # Aceeași piesă în alt folder (același conținut) și un „Bun” cu scor mare.
        session.add(
            Track(
                path="/alt/folder/1.mp3",
                file_hash="1",
                title="Slow Orbit (copie)",
                bpm=123.0,
                key_camelot="9A",
                energy=3,
                duration_s=422,
            )
        )
        session.add(
            Track(
                path="/m/boost.mp3",
                file_hash="boost",
                title="Boost",
                bpm=124.0,
                key_camelot="8A",
                energy=5,
                duration_s=300,
            )
        )
    paper = track_id(client, "Paper Lights")
    matches = client.get(f"/api/tracks/{paper}/matches").json()
    names = [(m["track"]["title"], m["label"]) for m in matches]
    assert names == [("Slow Orbit", "smooth"), ("Neon Tide", "smooth"), ("Boost", "good")]
    assert matches[2]["score"] > matches[1]["score"]  # scor mai mare, dar „Bun” vine după „Lin”


def test_matches_of_unanalyzed_track_is_empty(client: TestClient) -> None:
    assert client.get(f"/api/tracks/{track_id(client, 'Necunoscută')}/matches").json() == []


def test_matches_of_unknown_track_is_404(client: TestClient) -> None:
    assert client.get("/api/tracks/999999/matches").json()["error"]["code"] == "track_not_found"
