/**
 * Application core and router module.
 * Manages client-side routing and screen dispatching.
 * Handles dungeon combat, auth checks, and client-side navigation.
 */

import { fetchJson, clearAuthToken, setAuthToken } from './api.js';
import { formatDungeonMessage } from './helpers.js';
import { renderPlayerStatsInto, syncPlayerStatsInDom } from './components/player.js';
import { buildDungeonMarkup, applyDungeonCombatUpdate, showDungeonDefeatScreen } from './screens/dungeon-runtime.js';
import { state, getCharacterId } from './app-state.js';
import { renderLogin } from './screens/login.js';
import { renderCharacterSelect } from './screens/character-select.js';
import { renderHome } from './screens/home.js';
import { resetDungeonLoot } from './utils/state-updater.js';

const root = document.getElementById('root');

/**
 * Navigate by updating the hash-based client router.
 * Triggers re-render via hashchange listener.
 */
function navigateTo(path) {
  if (path === '/') {
    location.hash = '#/';
  } else {
    location.hash = `#${path}`;
  }
}

/**
 * Update the dungeon HUD with the current enemy stats.
 * Called after combat updates to reflect latest enemy state.
 */
function updateEnemyPanel(enemy) {
  if (!enemy) return;
  const enName = document.getElementById('enemy-name');
  const enLevel = document.getElementById('enemy-level');
  const enHealth = document.getElementById('enemy-health');
  const enDamage = document.getElementById('enemy-damage');
  if (enName) enName.textContent = `Enemy: ${enemy.name || 'None'}`;
  if (enLevel) enLevel.textContent = `${enemy.level || ''}`;
  if (enHealth) enHealth.textContent = `${enemy.health} / ${enemy.max_health} HP`;
  if (enDamage) enDamage.textContent = `${enemy.damage}`;
}

/**
 * Send an attack request and mirror the resulting combat state.
 * Handles player death, loot drops, and state synchronization.
 */
async function handleDungeonAttack() {
  const res = await fetchJson('/dungeon/attack', { method: 'POST' });
  if (!res.ok || !res.data) return;

  const dungeonState = res.data;
  const lootEl = document.getElementById('loot');
  applyDungeonCombatUpdate(dungeonState, {
    lootCounts: state.lootCounts,
    lootEl,
    setLastDungeonMessage: value => { state.lastDungeonMessage = value; }
  });

  if (dungeonState.player_died) {
    await showDungeonDefeatScreen({
      message: dungeonState.message || 'You were defeated and lost the loot from this dungeon run.',
      lootCounts: state.lootCounts,
      onExit: () => {
        resetDungeonLoot(state);
        navigateTo('/');
      }
    });
    return;
  }

  if (dungeonState.character) syncPlayerStatsInDom(dungeonState.character);
  if (dungeonState.enemy) updateEnemyPanel(dungeonState.enemy);
}

/**
 * Send a run request and update the dungeon screen based on the result.
 * Handles escape attempts, victory, and continued combat.
 */
async function handleDungeonRun() {
  const res = await fetchJson('/dungeon/run', { method: 'POST' });
  if (!res.ok || !res.data) return;

  const dungeonState = res.data;
  const dungeonMessage = document.getElementById('dungeon-message');
  if (dungeonMessage) {
    dungeonMessage.innerHTML = formatDungeonMessage(dungeonState.message || 'Action result');
  }

  if (dungeonState.player_died) {
    await showDungeonDefeatScreen({
      message: dungeonState.message || 'You were defeated and lost the loot from this dungeon run.',
      lootCounts: state.lootCounts,
      onExit: () => {
        resetDungeonLoot(state);
        navigateTo('/');
      }
    });
    return;
  }

  if (dungeonState.success) {
    setTimeout(async () => {
      resetDungeonLoot(state);
      navigateTo('/');
    }, 1500);
  } else {
    setTimeout(() => renderDungeon({ resetRunState: false }), 500);
  }
}

/**
 * Render the dungeon screen and bind combat controls to live actions.
 * Fetches the latest encounter and wires up attack/run/leave handlers.
 */
async function renderDungeon({ resetRunState = true } = {}) {
  if (resetRunState) resetDungeonLoot(state);
  state.lastDungeonMessage = null;
  root.innerHTML = `<div class="game-container"><div id="dungeon-content">Loading...</div></div>`;
  const content = document.getElementById('dungeon-content');

  const characterId = getCharacterId();
  if (!characterId) {
    navigateTo('/character-select');
    return;
  }

  const playerResponse = await fetchJson(`/characters/${characterId}`);
  if (playerResponse.ok && playerResponse.data) {
    state.player = playerResponse.data;
  }

  // The dungeon view always starts from the server-authoritative encounter state.
  const encounterResponse = await fetchJson('/dungeon/enter', { method: 'POST' });
  const enemy = encounterResponse.ok ? encounterResponse.data : { name: '', health: 0, max_health: 0, damage: 0, description: '' };

  const preface = `A wild ${enemy.name || 'creature'} appears! ${enemy.description || ''}`;
  const messageToShow = state.lastDungeonMessage || preface;
  content.innerHTML = buildDungeonMarkup(enemy, messageToShow);

  renderPlayerStatsInto(document.getElementById('player-stats-container'), state.player);
  state.lastDungeonMessage = null;

  document.getElementById('attack').addEventListener('click', event => {
    event.preventDefault();
    handleDungeonAttack();
  });
  document.getElementById('run').addEventListener('click', event => {
    event.preventDefault();
    handleDungeonRun();
  });
  document.getElementById('back').addEventListener('click', event => {
    event.preventDefault();
    fetchJson('/dungeon/leave', { method: 'POST' }).finally(() => {
      resetDungeonLoot(state);
      navigateTo('/');
    });
  });
}

/**
 * Resolve the current hash route and render the matching screen.
 * Handles authentication checks and dispatches to screen modules.
 */
async function route() {
  const hash = location.hash.replace('#', '') || '/';

  // Check authentication if accessing protected routes
  if (!state.currentUser && hash !== '/login') {
    const res = await fetchJson('/login/me');
    if (res.ok && res.data && res.data.user) {
      state.currentUser = res.data.user;
      if (res.data.character) state.player = res.data.character;
    } else {
      if (res.status === 401) clearAuthToken();
      location.hash = '#/login';
      return;
    }
  }

  // Dispatch to appropriate screen module
  const screenDeps = { fetchJson, navigateTo, setAuthToken, state };

  if (hash === '/login') return renderLogin(root, screenDeps);
  if (hash === '/character-select') return renderCharacterSelect(root, screenDeps);
  if (hash === '/' || hash === '') return state.player ? renderHome(root, screenDeps) : renderCharacterSelect(root, screenDeps);
  if (hash === '/dungeon') return renderDungeon();
  return renderHome(root, screenDeps);
}

// Initialize router on page load and hash changes
window.addEventListener('hashchange', route);
route();

export {
  navigateTo,
  route,
};