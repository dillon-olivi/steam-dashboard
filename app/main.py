from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cachetools import TTLCache
import random

from . import steam_client

app = FastAPI(title="Steam Stats Dashboard API")

# The frontend lives on GitHub Pages (a different origin than this API),
# so without CORS enabled the browser blocks every request by default.
# This is exactly the kind of real-world config that trips people up
# the first time they split frontend and backend across two hosts.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Public read-only data, safe to leave open for a demo
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Simple in-memory cache, 10 minute TTL. Steam stats don't change
# second to second, so this avoids hammering the upstream API every
# time someone reloads the page, and keeps the free-tier host from
# burning its rate limit during a busy demo day.
summary_cache: TTLCache = TTLCache(maxsize=100, ttl=600)
games_cache: TTLCache = TTLCache(maxsize=100, ttl=600)

# Steam has no "give me a random public user" endpoint, so instead we
# keep a small pool of known profiles and, at request time, try them
# until we find one that's actually public right now. Self-healing:
# if one goes private later, the demo just moves on to the next
# candidate instead of breaking. Mix of raw Steam IDs and vanity
# names, both are resolved the same way via resolve_identifier().
DEMO_PROFILE_CANDIDATES = [
    "76561198114503273",
    "76561197980383022",
    "76561198052841376",
    "chorzo",
    "76561199500454712",
    "76561198116713060",
    "glitterbanq",
    "tbombb",
    "NewbOvision",
    "76561199211346938",
    "76561198172164646",
]


@app.get("/api/demo-profile")
async def demo_profile():
    """Tries each candidate Steam ID in random order and returns the
    first one that's actually public and has visible game data right
    now. This is what makes 'Load Demo Profile' reliable long-term,
    it doesn't trust any single hardcoded ID to stay public forever."""
    candidates = DEMO_PROFILE_CANDIDATES.copy()
    random.shuffle(candidates)

    for candidate in candidates:
        try:
            resolved_id = await steam_client.resolve_identifier(candidate)
            await steam_client.get_player_summary(resolved_id)
            await steam_client.get_owned_games(resolved_id)
            return {"steam_id": resolved_id}
        except steam_client.SteamAPIError:
            continue  # This one's private, invalid, or unavailable, try the next

    raise HTTPException(
        status_code=503,
        detail="None of the demo profiles are public right now, try a manual Steam ID instead",
    )


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/player/{steam_id}")
async def player_summary(steam_id: str):
    try:
        resolved_id = await steam_client.resolve_identifier(steam_id)
    except steam_client.SteamAPIError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if resolved_id in summary_cache:
        return summary_cache[resolved_id]
    try:
        summary = await steam_client.get_player_summary(resolved_id)
    except steam_client.SteamAPIError as e:
        raise HTTPException(status_code=404, detail=str(e))
    summary_cache[resolved_id] = summary
    return summary


@app.get("/api/player/{steam_id}/games")
async def player_games(steam_id: str, limit: int = 10):
    try:
        resolved_id = await steam_client.resolve_identifier(steam_id)
    except steam_client.SteamAPIError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if resolved_id in games_cache:
        games = games_cache[resolved_id]
    else:
        try:
            games = await steam_client.get_owned_games(resolved_id)
        except steam_client.SteamAPIError as e:
            raise HTTPException(status_code=404, detail=str(e))
        games_cache[resolved_id] = games

    total_hours = round(sum(g.get("playtime_forever", 0) for g in games) / 60, 1)
    return {
        "total_games": len(games),
        "total_hours_played": total_hours,
        "top_games": [
            {
                "name": g.get("name"),
                "hours_played": round(g.get("playtime_forever", 0) / 60, 1),
                "icon_url": f"https://media.steampowered.com/steamcommunity/public/images/apps/{g['appid']}/{g.get('img_icon_url')}.jpg" if g.get("img_icon_url") else None,
            }
            for g in games[:limit]
        ],
    }
