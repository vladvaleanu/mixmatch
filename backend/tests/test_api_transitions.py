import pytest
from fastapi.testclient import TestClient

from mixmatch.db.models import Track
from mixmatch.db.session import SessionLocal


@pytest.fixture
def ids(client: TestClient) -> list[int]:
    rows = [  # titlu, bpm, ton, energie
        ("Slow Orbit", 123.0, "9A", 3),
        ("Paper Lights", 124.0, "8A", 4),
        ("Low Sun", 126.0, "3B", 5),
        ("Necunoscută", None, None, None),
    ]
    with SessionLocal.begin() as session:
        tracks = [
            Track(
                path=f"/t/{i}",
                file_hash=f"t{i}",
                title=t,
                bpm=bpm,
                key_camelot=key,
                energy=e,
                first_beat_s=0.2 if bpm else None,
                duration_s=360,
                outro_bars=32,
                intro_bars=16,
                loudness_lufs=-9.0,
            )  # fmt: skip
            for i, (t, bpm, key, e) in enumerate(rows)
        ]
        session.add_all(tracks)
        session.flush()
        return [t.id for t in tracks]


def mix_with(client: TestClient, track_ids: list[int]) -> int:
    return client.post("/api/mixes", json={"track_ids": track_ids}).json()["id"]


def test_default_plan(client: TestClient, ids: list[int]) -> None:
    mix_id = mix_with(client, ids[:3])
    out = client.get(f"/api/mixes/{mix_id}/transitions/1/plan").json()
    assert (out["from_track"]["title"], out["to_track"]["title"]) == ("Slow Orbit", "Paper Lights")
    assert (out["label"], out["key_label"], out["tempo_label"]) == ("smooth", "smooth", "smooth")
    plan = out["plan"]
    assert (plan["style"], plan["length_bars"], plan["a_out_auto"]) == ("eq_swap", 16, True)
    assert {a["target"] for a in plan["automations"]} == {
        "a_volume",
        "b_volume",
        "a_bass",
        "b_bass",
    }
    assert plan["gain_a_db"] == -3.0


def test_patch_length_style_and_points(client: TestClient, ids: list[int]) -> None:
    mix_id = mix_with(client, ids[:3])
    out = client.patch(
        f"/api/mixes/{mix_id}/transitions/1",
        json={"length_bars": 32, "style": "crossfade", "a_out_s": 100.0},
    ).json()
    plan = out["plan"]
    assert (plan["length_bars"], plan["style"], plan["a_out_auto"]) == (32, "crossfade", False)
    assert plan["a_out_s"] != 100.0  # lipit de frază
    again = client.get(f"/api/mixes/{mix_id}/transitions/1/plan").json()["plan"]
    assert again == plan

    reset = client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"reset_points": True}).json()
    assert reset["plan"]["a_out_auto"] is True
    assert reset["plan"]["length_bars"] == 32  # restul rămâne


def test_settings_follow_the_pair(client: TestClient, ids: list[int]) -> None:
    slow, paper, low = ids[:3]
    mix_id = mix_with(client, [slow, paper, low])
    client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"style": "cut"})

    client.put(f"/api/mixes/{mix_id}/items", json={"track_ids": [low, slow, paper]})
    moved = client.get(
        f"/api/mixes/{mix_id}/transitions/2/plan"
    ).json()  # aceeași pereche, altă poziție
    assert moved["plan"]["style"] == "cut"
    assert (
        client.get(f"/api/mixes/{mix_id}/transitions/1/plan").json()["plan"]["style"] == "eq_swap"
    )


def test_auto_choice_uses_the_label(client: TestClient, ids: list[int]) -> None:
    slow, paper, low = ids[:3]
    mix_id = mix_with(client, [slow, paper, low])
    smooth = client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"auto": True}).json()
    caution = client.patch(f"/api/mixes/{mix_id}/transitions/2", json={"auto": True}).json()
    assert (smooth["plan"]["length_bars"], smooth["plan"]["style"]) == (32, "eq_swap")
    assert caution["label"] == "caution"
    assert (caution["plan"]["length_bars"], caution["plan"]["style"]) == (8, "echo_out")


def test_errors(client: TestClient, ids: list[int]) -> None:
    mix_id = mix_with(client, [ids[0], ids[3]])
    assert (
        client.get(f"/api/mixes/{mix_id}/transitions/1/plan").json()["error"]["code"]
        == "not_analyzed"
    )
    assert (
        client.get(f"/api/mixes/{mix_id}/transitions/5/plan").json()["error"]["code"]
        == "transition_not_found"
    )
    assert client.get(f"/api/mixes/{mix_id}/transitions/0/plan").status_code == 404
    bad = client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"length_bars": 12})
    assert bad.status_code == 422


def test_nudge_is_saved_and_survives_auto(client: TestClient, ids: list[int]) -> None:
    mix_id = mix_with(client, ids[:3])
    base = client.get(f"/api/mixes/{mix_id}/transitions/1/plan").json()["plan"]
    nudged = client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"b_nudge_s": -0.03}).json()
    assert nudged["plan"]["b_nudge_s"] == -0.03
    assert nudged["plan"]["b_start_s"] == pytest.approx(
        base["b_start_s"] + 0.03 * base["speed_b"], abs=1e-3
    )
    auto = client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"auto": True}).json()
    assert auto["plan"]["b_nudge_s"] == -0.03  # corecția ține de pereche, nu de stil
    reset = client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"reset_points": True}).json()
    assert reset["plan"]["b_nudge_s"] == -0.03
    assert (
        client.patch(f"/api/mixes/{mix_id}/transitions/1", json={"b_nudge_s": 3}).status_code == 422
    )
