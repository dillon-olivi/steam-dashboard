// Backend deployed on Render, see README for redeploy/setup steps.
const API_BASE_URL = "https://steam-dashboard-qlvr.onrender.com";

// The demo profile is now found dynamically via the backend's
// /api/demo-profile endpoint (see below), instead of trusting one
// hardcoded ID to stay public forever.

const statusEl = document.getElementById("status");
const profileEl = document.getElementById("profile");
const gamesListEl = document.getElementById("games-list");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.className = isError ? "error" : "";
}

async function loadProfile(steamId) {
  if (API_BASE_URL.startsWith("REPLACE_WITH")) {
    setStatus(
      "Backend not deployed yet, see the README for the one-time Render deployment steps.",
      true
    );
    return;
  }

  profileEl.classList.add("hidden");
  gamesListEl.innerHTML = "";
  setStatus("Loading, the free-tier backend may take up to 30-50 seconds to wake up on the first request today\u2026");

  try {
    const [summaryRes, gamesRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/player/${steamId}`),
      fetch(`${API_BASE_URL}/api/player/${steamId}/games?limit=8`),
    ]);

    if (!summaryRes.ok) throw new Error((await summaryRes.json()).detail || "Profile not found");
    if (!gamesRes.ok) throw new Error((await gamesRes.json()).detail || "Game data not available");

    const summary = await summaryRes.json();
    const games = await gamesRes.json();

    document.getElementById("avatar").src = summary.avatarfull || "";
    document.getElementById("persona-name").textContent = summary.personaname || "Unknown Player";
    document.getElementById("totals").textContent =
      `${games.total_games} games owned \u00b7 ${games.total_hours_played} hours played total`;

    const maxHours = Math.max(...games.top_games.map(g => g.hours_played), 1);
    gamesListEl.innerHTML = games.top_games
      .map(g => `
        <div class="game-row">
          <span class="game-name">${g.name}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:${(g.hours_played / maxHours) * 100}%"></div>
          </div>
          <span class="game-hours">${g.hours_played}h</span>
        </div>
      `)
      .join("");

    profileEl.classList.remove("hidden");
    setStatus("");
  } catch (err) {
    setStatus(err.message, true);
  }
}

// Accepts a raw SteamID64, a full /profiles/ URL, a full /id/ vanity
// URL, or just a bare vanity name typed directly, and returns
// whatever identifier the backend should resolve. The backend (via
// resolve_identifier) handles turning a vanity name into a real ID,
// this function's only job is stripping the surrounding URL if there
// is one.
function extractSteamId(raw) {
  const trimmed = raw.trim();
  const profileUrlMatch = trimmed.match(/steamcommunity\.com\/profiles\/(\d+)/i);
  if (profileUrlMatch) return profileUrlMatch[1];
  const vanityUrlMatch = trimmed.match(/steamcommunity\.com\/id\/([^\/]+)/i);
  if (vanityUrlMatch) return vanityUrlMatch[1];
  return trimmed; // bare ID or bare vanity name, let the backend resolve it
}

document.getElementById("lookup-btn").addEventListener("click", () => {
  const raw = document.getElementById("steamid-input").value;
  if (!raw.trim()) {
    setStatus("Enter a Steam ID, vanity name, or profile URL first, or click Load Demo Profile.", true);
    return;
  }
  loadProfile(extractSteamId(raw));
});

document.getElementById("demo-btn").addEventListener("click", async () => {
  if (API_BASE_URL.startsWith("REPLACE_WITH")) {
    setStatus("Backend not deployed yet, see the README for deployment steps.", true);
    return;
  }
  setStatus("Finding a public demo profile\u2026");
  try {
    const res = await fetch(`${API_BASE_URL}/api/demo-profile`);
    if (!res.ok) throw new Error((await res.json()).detail || "No public demo profile available right now");
    const { steam_id } = await res.json();
    document.getElementById("steamid-input").value = steam_id;
    loadProfile(steam_id);
  } catch (err) {
    setStatus(err.message, true);
  }
});
