# Steam Stats Dashboard

A full-stack application that looks up a public Steam account and shows their game library, total hours played, and top games by playtime, pulled live from Steam's own API.

**Live Demo:** [dillon-olivi.github.io/steam-dashboard](https://dillon-olivi.github.io/steam-dashboard/)
**Repository:** [github.com/dillon-olivi/steam-dashboard](https://github.com/dillon-olivi/steam-dashboard)

## Overview

This project uses a Python backend and static frontend deployed independently.

The FastAPI backend proxies Steam's Web API so API credentials remain server-side and browser CORS restrictions are avoided. It accepts a Steam ID, profile URL, or vanity name, resolves the account, calculates total playtime and top games, and caches repeated requests to reduce unnecessary upstream API calls.

I built it to demonstrate backend API development, third-party integration, caching, error handling, automated testing, and independent frontend/backend deployment.

## Engineering highlights

* Built a FastAPI backend that proxies Steam's `GetPlayerSummaries`, `GetOwnedGames`, and `ResolveVanityURL` endpoints
* Resolved CORS restrictions and kept API credentials server-side instead of exposed in client code
* Implemented response caching (`cachetools`) to reduce repeat calls to the upstream API
* Built a fallback demo-profile system that automatically selects another public profile when the current demo account becomes unavailable
* Added graceful error handling for private, invalid, or unavailable profiles
* Deployed the backend independently (Render) from the static frontend (GitHub Pages)
* Integrated Claude Code directly into the CI pipeline to review pull requests and flag test coverage gaps

## Tech stack

* Python
* FastAPI
* httpx
* pytest / pytest-mock
* JavaScript (vanilla frontend)
* GitHub Actions
* GitHub Pages
* Render

## Testing

The project uses a fully mocked automated test suite:

**API tests**
Verify backend responses for player summaries, game libraries, and the demo-profile fallback logic, with Steam's API fully mocked so tests run without real credentials or network calls.

**CI-integrated AI review**
Claude Code runs inside the CI pipeline on every pull request, reading the diff and the test coverage output to flag any changed code that lacks coverage.

This approach provides coverage at the service level while keeping the suite fast and reliable in CI.

## CI/CD

GitHub Actions runs the automated test suite on every push. A separate workflow runs Claude Code against every pull request, using Anthropic's official `claude-code-action`, to review the diff and post a plain-language summary as a PR comment.

The AI review workflow uses limited permissions and is kept separate from deployment decisions.

## Project structure

```text
app/
  main.py
  steam_client.py
docs/
  index.html
  style.css
  app.js
tests/
  test_api.py
.github/
  workflows/
    tests.yml
    claude-review.yml
```

## Deploying this yourself (if you fork it)

1. Get a free Steam Web API key at [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. Deploy the backend to Render (free tier): connect this repo, build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and add a `STEAM_API_KEY` environment variable
3. In `docs/app.js`, replace `API_BASE_URL` with your Render URL
4. Turn on GitHub Pages: Settings → Pages → Deploy from branch → `main` → `/docs`

Render's free tier sleeps after inactivity, so the first request after a while can take 30 to 50 seconds to wake back up.

## What I'd add next

* Rate limiting on my own API, not just caching
* A "compare two profiles" view
* Redis instead of in-memory caching, so the cache survives a restart

## About

Built by **Dillon Olivi** as part of my software engineering portfolio, with a focus on backend development, third-party API integration, automated testing, and reliable systems.
