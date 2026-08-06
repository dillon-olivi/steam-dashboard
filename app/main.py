from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cachetools import TTLCache

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


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/player/{steam_id}")
async def player_summary(steam_id: str):
    if steam_id in summary_cache:
        return summary_cache[steam_id]
    try:
        summary = await steam_client.get_player_summary(steam_id)
    except steam_client.SteamAPIError as e:
        raise HTTPException(status_code=404, detail=str(e))
    summary_cache[steam_id] = summary
    return summary


@app.get("/api/player/{steam_id}/games")
async def player_games(steam_id: str, limit: int = 10):
    if steam_id in games_cache:
        games = games_cache[steam_id]
    else:
        try:
            games = await steam_client.get_owned_games(steam_id)
        except steam_client.SteamAPIError as e:
            raise HTTPException(status_code=404, detail=str(e))
        games_cache[steam_id] = games

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
