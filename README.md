# Steam Stats Dashboard

**[Live demo](https://dillon-olivi.github.io/steam-dashboard/)** — enter
any public Steam profile (ID, vanity URL, or profile URL) or click
"Load Demo Profile" for an instant real result. No download, no setup.

Built by [Dillon Olivi](https://www.dillonolivi-gamedesignportfolio.com/) · [GitHub](https://github.com/dillon-olivi)

---

## What this is

A full-stack web app that looks up a Steam account and shows their
game library, total hours played, and top games by playtime, pulled
live from Steam's own API.

## What it demonstrates

- **Full-stack architecture** — a Python (FastAPI) backend deployed
  separately from a static frontend (GitHub Pages), talking to each
  other across hosts, the way most real production systems are
  actually structured
- **Third-party API integration** — server-side proxying to work
  around Steam's CORS restrictions, with API credentials kept out of
  client-side code entirely
- **Real-world resilience** — a fallback system that automatically
  finds a working public profile for the demo button, and graceful
  error handling when a profile is private or invalid
- **Performance-minded backend design** — response caching to avoid
  hammering the upstream API on repeat lookups
- **Automated testing** — a full pytest suite with Steam's API fully
  mocked, so tests run fast and reliably in CI without needing real
  credentials
- **AI integrated into the CI/CD pipeline itself** — pull requests are
  automatically reviewed by Claude Code for test coverage gaps, not
  just used as a coding assistant during development

## Stack

FastAPI · httpx · pytest + pytest-mock · vanilla JS frontend ·
GitHub Actions · Render

## Related projects

- [release-readiness-demo](https://github.com/dillon-olivi/release-readiness-demo) — test automation & CI/CD focused
- [raid-tracker](https://github.com/dillon-olivi/raid-tracker) — full-stack CRUD app with a relational database

---

## Why there's a backend at all

Two real constraints forced this, not just "because full-stack projects
usually have one":

1. **Steam's API doesn't support CORS**, a browser calling it directly
   gets blocked, full stop. A server-side proxy is the standard fix.
2. **The Steam API key shouldn't live in frontend code.** Anyone could
   view-source it and use it as their own. It needs to sit server-side
   as an environment variable.

## Architecture

- **`/app`** — FastAPI backend: proxies Steam's `GetPlayerSummaries`,
  `GetOwnedGames`, and `ResolveVanityURL` endpoints, computes total
  hours and top games server-side, and caches responses for 10 minutes
  (`cachetools`) so repeat lookups don't re-hit Steam's API or burn
  the free-tier rate limit
- **`/docs`** — static frontend (vanilla JS, no framework) deployed via
  GitHub Pages, calls the deployed backend over `fetch`. Accepts a raw
  Steam ID, a `/profiles/` URL, a `/id/` vanity URL, or a bare vanity
  name, the backend resolves all of these to a real Steam ID
- **`/tests`** — API tests with Steam's responses fully mocked
  (`pytest-mock`), so the suite runs in CI without needing a real API
  key or making real network calls
- **`.github/workflows`** — CI runs the test suite, and Claude Code
  reviews pull requests, on every push

## The demo profile fallback

Steam has no "give me a random public user" endpoint, so `/api/demo-profile`
keeps a small pool of known profiles (mix of raw IDs and vanity names)
and, at request time, tries them in random order until it finds one
that's actually public right now. Self-healing: if one goes private
later, the demo just moves on to the next candidate instead of breaking.

## AI integrated into CI/CD

Beyond using AI as a coding assistant, this repo runs **Claude Code
directly inside the CI pipeline** (`.github/workflows/claude-review.yml`),
using Anthropic's official `claude-code-action`. On every pull request it:

- Reads the diff and reviews the actual code change
- Reads the pytest coverage output and flags any changed code that
  lacks test coverage
- Posts a plain-language summary as a PR comment

Claude Code Action also supports connecting **MCP servers** during CI
runs. I kept this demo to a single workflow without extra services,
but the `mcp_config` option is where that would plug in.

**Security note**: this workflow intentionally runs with narrow,
read-focused permissions and never triggers on `pull_request_target`
against untrusted fork code, since Claude Code Action has documented
prompt-injection and secret-exfiltration risks when misconfigured.

## Deploying this yourself (if you fork it)

**1. Get a free Steam Web API key**
[steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)

**2. Deploy the backend to Render (free tier)**
- Create an account at [render.com](https://render.com)
- New → Web Service → connect this GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add an environment variable: `STEAM_API_KEY` = your key from step 1

Note: Render's free tier sleeps after inactivity, the first request
after a while takes 30 to 50 seconds to wake back up.

**3. Point the frontend at your backend**
In `docs/app.js`, replace `API_BASE_URL` with your Render URL.

**4. Turn on GitHub Pages**
Settings → Pages → Deploy from branch → `main` → `/docs`.

## Running the backend locally

```bash
pip install -r requirements.txt
export STEAM_API_KEY=your_key_here
uvicorn app.main:app --reload
```

## Running the tests

```bash
pytest -v
```

No API key needed, all Steam responses are mocked.

## A note on AI assistance

I used Claude to help scaffold the FastAPI structure, the CORS/caching
setup, and the mocked test patterns. The architecture decisions, why a
backend is needed here, what to cache and for how long, and what the
API should compute server-side versus leave to the frontend, are the
actual engineering judgment calls, and those are mine.

## What I'd add next

- Rate limiting on my own API, not just caching
- A "compare two profiles" view
- Redis instead of in-memory caching, so the cache survives a restart
