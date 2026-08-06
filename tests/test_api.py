import pytest
from fastapi.testclient import TestClient
from app.main import app, summary_cache, games_cache
from app import steam_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_caches():
    summary_cache.clear()
    games_cache.clear()
    yield


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_player_summary_success(mocker):
    mocker.patch(
        "app.steam_client.get_player_summary",
        return_value={"personaname": "TestPlayer", "avatarfull": "http://example.com/avatar.jpg"},
    )
    response = client.get("/api/player/12345")
    assert response.status_code == 200
    assert response.json()["personaname"] == "TestPlayer"


def test_player_summary_not_found(mocker):
    mocker.patch(
        "app.steam_client.get_player_summary",
        side_effect=steam_client.SteamAPIError("No player found"),
    )
    response = client.get("/api/player/00000")
    assert response.status_code == 404


def test_player_games_computes_totals_and_sorts_by_playtime(mocker):
    mocker.patch(
        "app.steam_client.get_owned_games",
        return_value=[
            {"appid": 1, "name": "Diablo IV", "playtime_forever": 6000, "img_icon_url": "abc"},
            {"appid": 2, "name": "World of Warcraft", "playtime_forever": 12000, "img_icon_url": "def"},
        ],
    )
    response = client.get("/api/player/12345/games")
    assert response.status_code == 200
    body = response.json()
    assert body["total_games"] == 2
    assert body["total_hours_played"] == 300.0
    # Highest playtime should be first
    assert body["top_games"][0]["name"] == "World of Warcraft"


def test_player_games_respects_limit(mocker):
    mocker.patch(
        "app.steam_client.get_owned_games",
        return_value=[
            {"appid": i, "name": f"Game {i}", "playtime_forever": i * 10, "img_icon_url": "x"}
            for i in range(20)
        ],
    )
    response = client.get("/api/player/12345/games?limit=5")
    assert len(response.json()["top_games"]) == 5


def test_second_request_uses_cache(mocker):
    mock = mocker.patch(
        "app.steam_client.get_player_summary",
        return_value={"personaname": "CachedPlayer"},
    )
    client.get("/api/player/999")
    client.get("/api/player/999")
    # Should only hit the "Steam API" once, second call served from cache
    assert mock.call_count == 1
