// IMPORTANT: after deploying the backend (see README), replace this
// with your actual Render URL, e.g. "https://steam-dashboard-api.onrender.com"
const API_BASE_URL = "REPLACE_WITH_YOUR_DEPLOYED_BACKEND_URL";

// A well-known public Steam profile, used so "Load Demo Profile" always
// works even if a visitor doesn't have their own Steam ID handy.
const DEMO_STEAM_ID = "76561197960287930";

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

document.getElementById("lookup-btn").addEventListener("click", () => {
  const id = document.getElementById("steamid-input").value.trim();
  if (!id) {
    setStatus("Enter a Steam ID first, or click Load Demo Profile.", true);
    return;
  }
  loadProfile(id);
});

document.getElementById("demo-btn").addEventListener("click", () => {
  document.getElementById("steamid-input").value = DEMO_STEAM_ID;
  loadProfile(DEMO_STEAM_ID);
});
