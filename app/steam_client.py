import os
import httpx

STEAM_API_KEY = os.environ.get("STEAM_API_KEY", "")
BASE_URL = "https://api.steampowered.com"


class SteamAPIError(Exception):
    pass


async def get_player_summary(steam_id: str) -> dict:
    url = f"{BASE_URL}/ISteamUser/GetPlayerSummaries/v2/"
    params = {"key": STEAM_API_KEY, "steamids": steam_id}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
    if response.status_code != 200:
        raise SteamAPIError(f"Steam API returned {response.status_code}")
    players = response.json().get("response", {}).get("players", [])
    if not players:
        raise SteamAPIError("No player found for that Steam ID, profile may be private or the ID is wrong")
    return players[0]


async def resolve_vanity_url(vanity_name: str) -> str:
    """Steam profile URLs like steamcommunity.com/id/chorzo/ use a
    custom nickname instead of the real numeric Steam ID. This asks
    Steam 'what ID does this nickname actually belong to?' so the rest
    of the app only ever has to deal with real numeric IDs."""
    url = f"{BASE_URL}/ISteamUser/ResolveVanityURL/v1/"
    params = {"key": STEAM_API_KEY, "vanityurl": vanity_name}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
    if response.status_code != 200:
        raise SteamAPIError(f"Steam API returned {response.status_code}")
    result = response.json().get("response", {})
    if result.get("success") != 1:
        raise SteamAPIError(f"No Steam account found for '{vanity_name}'")
    return result["steamid"]


async def resolve_identifier(identifier: str) -> str:
    """Accepts either a raw numeric Steam ID or a vanity name, and
    always returns a real numeric Steam ID."""
    if identifier.isdigit():
        return identifier
    return await resolve_vanity_url(identifier)


async def get_owned_games(steam_id: str) -> list[dict]:
    url = f"{BASE_URL}/IPlayerService/GetOwnedGames/v1/"
    params = {
        "key": STEAM_API_KEY,
        "steamid": steam_id,
        "include_appinfo": 1,
        "include_played_free_games": 1,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
    if response.status_code != 200:
        raise SteamAPIError(f"Steam API returned {response.status_code}")
    games = response.json().get("response", {}).get("games", [])
    if not games:
        raise SteamAPIError("No game library data, profile's game details may be private")
    return sorted(games, key=lambda g: g.get("playtime_forever", 0), reverse=True)
