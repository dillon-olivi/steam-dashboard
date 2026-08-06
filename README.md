# Steam Stats Dashboard

**[Live demo](https://dillon-olivi.github.io/steam-dashboard/)**, enter
any public Steam ID or click "Load Demo Profile" for instant real data.
No download required.

## What this demonstrates

Most of my other projects are self-contained. This one specifically
shows working with a **third-party API in a real deployed environment**,
frontend on one host (GitHub Pages), backend on another (Render), talking
to each other across origins, which is how most real production systems
are actually structured.

## Why there's a backend at all

Two real constraints forced this, not just "because full-stack projects
usually have one":

1. **Steam's API doesn't support CORS**, a browser calling it directly
   gets blocked, full stop. A server-side proxy is the standard fix.
2. **The Steam API key shouldn't live in frontend code.** Anyone could
   view-source it and use it as their own. It needs to sit server-side
   as an environment variable.

## Architecture

- **`/app`** — FastAPI backend: proxies Steam's `GetPlayerSummaries` and
  `GetOwnedGames` endpoints, computes total hours and top games
  server-side, and caches responses for 10 minutes (`cachetools`) so
  repeat lookups don't re-hit Steam's API or burn the free-tier rate
  limit
- **`/docs`** — static frontend (vanilla JS, no framework) deployed via
  GitHub Pages, calls the deployed backend over `fetch`
- **`/tests`** — API tests with Steam's responses fully mocked
  (`pytest-mock`), so the suite runs in CI without needing a real API
  key or making real network calls
- **`.github/workflows`** — CI runs the test suite on every push

## AI integrated into CI/CD

Beyond using AI as a coding assistant, this repo runs **Claude Code
directly inside the CI pipeline** (`.github/workflows/claude-review.yml`),
using Anthropic's official `claude-code-action`. On every pull request it:

- Reads the diff and reviews the actual code change
- Reads the pytest coverage output and flags any changed code that
  lacks test coverage
- Posts a plain-language summary as a PR comment

Claude Code Action also supports connecting **MCP servers** during CI
runs, for example a database MCP to validate migrations, or an issue
tracker MCP to auto-file follow-ups. I kept this demo to a single
workflow without extra services, but the `mcp_config` option is where
that would plug in.

**Security note**: this workflow intentionally runs with narrow,
read-focused permissions and never triggers on `pull_request_target`
against untrusted fork code, since Claude Code Action has documented
prompt-injection and secret-exfiltration risks when misconfigured. An
AI agent with write access to your CI pipeline is a real attack
surface, not just a convenience feature, and treating it that way
matters as much as setting it up in the first place.



**1. Get a free Steam Web API key**
[steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey),
takes a minute, just needs a domain name (your GitHub Pages URL works).

**2. Deploy the backend to Render (free tier)**
- Create a account at [render.com](https://render.com)
- New → Web Service → connect this GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add an environment variable: `STEAM_API_KEY` = your key from step 1
- Deploy, Render gives you a URL like `https://your-app.onrender.com`

Note: Render's free tier sleeps after inactivity, the first request
after a while takes 30 to 50 seconds to wake back up. The demo page
tells visitors this so it doesn't look broken.

**3. Point the frontend at your backend**
In `docs/app.js`, replace `API_BASE_URL` with your Render URL from
step 2.

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
backend is needed here (CORS + secret protection), what to cache and
for how long, and what the API should compute server-side versus leave
to the frontend, are the actual engineering judgment calls, and those
are mine.

## What I'd add next

- Rate limiting on my own API, not just caching, to protect the Steam
  key from abuse if this got heavy traffic
- A "compare two profiles" view
- Redis instead of in-memory caching, so the cache survives a backend
  restart
