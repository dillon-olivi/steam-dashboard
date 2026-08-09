// Backend deployed on Render, see DEVELOPMENT.md for redeploy/setup steps.
const API_BASE_URL = "https://steam-dashboard-qlvr.onrender.com";

const statusEl = document.getElementById("status");
const spinnerEl = document.getElementById("spinner");
const profileEl = document.getElementById("profile");
const gamesSectionEl = document.getElementById("games-section");
const gamesListEl = document.getElementById("games-list");

function setStatus(message, isError = false, loading = false) {
  statusEl.textContent = message;
  statusEl.className = isError ? "error" : "";
  spinnerEl.classList.toggle("hidden", !loading);
}

async function loadProfile(steamId) {
  profileEl.classList.add("hidden");
  gamesSectionEl.classList.add("hidden");
  gamesListEl.innerHTML = "";
  setStatus("Loading, the free-tier backend may take up to 30-50 seconds to wake up on the first request today\u2026", false, true);

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
    document.getElementById("badge-games").textContent = `${games.total_games} games`;
    document.getElementById("badge-hours").textContent = `${games.total_hours_played} hrs played`;

    const maxHours = Math.max(...games.top_games.map(g => g.hours_played), 1);
    gamesListEl.innerHTML = games.top_games
      .map(g => `
        <div class="game-row">
          ${g.icon_url ? `<img class="game-icon" src="${g.icon_url}" alt="" />` : `<div class="game-icon"></div>`}
          <span class="game-name" title="${g.name}">${g.name}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:${(g.hours_played / maxHours) * 100}%"></div>
          </div>
          <span class="game-hours">${g.hours_played}h</span>
        </div>
      `)
      .join("");

    profileEl.classList.remove("hidden");
    gamesSectionEl.classList.remove("hidden");
    setStatus("");
  } catch (err) {
    setStatus(err.message, true, false);
  }
}

// Accepts a raw SteamID64, a full /profiles/ URL, a full /id/ vanity
// URL, or just a bare vanity name typed directly. The backend resolves
// vanity names to real IDs, this only strips the surrounding URL.
function extractSteamId(raw) {
  const trimmed = raw.trim();
  const profileUrlMatch = trimmed.match(/steamcommunity\.com\/profiles\/(\d+)/i);
  if (profileUrlMatch) return profileUrlMatch[1];
  const vanityUrlMatch = trimmed.match(/steamcommunity\.com\/id\/([^\/]+)/i);
  if (vanityUrlMatch) return vanityUrlMatch[1];
  return trimmed;
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
  setStatus("Finding a public demo profile\u2026", false, true);
  try {
    const res = await fetch(`${API_BASE_URL}/api/demo-profile`);
    if (!res.ok) throw new Error((await res.json()).detail || "No public demo profile available right now");
    const { steam_id } = await res.json();
    document.getElementById("steamid-input").value = steam_id;
    loadProfile(steam_id);
  } catch (err) {
    setStatus(err.message, true, false);
  }
});
