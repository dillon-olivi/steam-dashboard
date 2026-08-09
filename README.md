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
  automatically reviewed by Claude Code for test coverage gaps

## Stack

FastAPI · httpx · pytest + pytest-mock · vanilla JS frontend ·
GitHub Actions · Render

## Related projects

- [release-readiness-demo](https://github.com/dillon-olivi/release-readiness-demo) — test automation & CI/CD focused
  
---

## Why there's a backend at all

Two real constraints forced this:

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

## A note on AI assistance

I used Claude to help scaffold the FastAPI structure, the CORS/caching
setup, and the mocked test patterns. The architecture decisions, why a
backend is needed here, what to cache and for how long, and what the
API should compute server-side versus leave to the frontend, are the
actual engineering judgment calls that were mine to make. I take pride
in the work I produce and rely on my own skills like a traditional 
carpenter would when crafting a chair. But sometimes, metaphorically, 
power tools can make the process faster without losing too much 
quality. That's a fine line I take seriously and pay close attention to.

