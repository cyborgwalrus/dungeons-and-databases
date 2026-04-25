/**
 * Application core and router module.
 * Manages client-side routing and screen dispatching.
 * Handles dungeon combat, auth checks, and client-side navigation.
 */

import { fetchJson, clearAuthToken, setAuthToken } from './api.js';
import { escapeHtml, formatDungeonMessage } from './helpers.js';
import { buildScreenShell } from './ui.js';
import { renderPlayerStatsInto, syncPlayerStatsInDom } from './components/player.js';
import { buildDungeonMarkup, applyDungeonCombatUpdate, renderLootPanel, showDungeonDefeatScreen, updateDungeonActionLabels } from './screens/dungeon-runtime.js';
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
  const enemyBar = document.getElementById('enemy-health-bar');
  if (enName) enName.textContent = `Enemy: ${enemy.name}`;
  if (enLevel) enLevel.textContent = `${enemy.level}`;
  if (enHealth) enHealth.textContent = `${enemy.health} / ${enemy.max_health} HP`;
  if (enDamage) enDamage.textContent = `${enemy.damage}`;
  if (enemyBar) {
    const currentHealth = Math.max(0, Number(enemy.health) || 0);
    const maxHealth = Math.max(1, Number(enemy.max_health) || 1);
    const fill = enemyBar.querySelector('.vertical-health-bar-fill');
    if (fill) fill.style.height = `${Math.max(0, Math.min(1, currentHealth / maxHealth)) * 100}%`;
    enemyBar.dataset.health = String(currentHealth);
    enemyBar.dataset.maxHealth = String(maxHealth);
  }
}

/** Build the enemy view model directly from the combat payload. */
function buildDungeonEnemy(combat) {
  if (!combat?.enemy) {
    return null;
  }
  return { ...combat.enemy };
}

/** Render a dungeon-specific error state in the content area. */
function renderDungeonError(message) {
  const content = document.getElementById('dungeon-content');
  if (!content) return;
  content.innerHTML = buildScreenShell({
    className: 'screen-shell--game',
    title: 'Dungeons & Databases',
    subtitle: 'Prepare for combat',
    sections: [{
      className: 'screen-panel screen-panel--dark',
      body: `<div class="dungeon-message"><div class="dungeon-message-frame"><div class="dungeon-message-status dungeon-message-defeat-text">Defeat!</div><div class="dungeon-message-body"><div class="dungeon-message-line">${escapeHtml(message)}</div></div></div></div>`,
    }],
  });
  state.activeCombat = null;
  state.dungeonActionMode = 'run';
}

/**
 * Send an attack request and mirror the resulting combat state.
 * Handles player death, loot drops, and state synchronization.
 */
async function handleDungeonAttack() {
  if (!state.activeCombat?.id) return;
  const action = state.dungeonActionMode === 'deeper' ? 'deeper' : 'attack';
  const res = await fetchJson(`/combats/${state.activeCombat.id}/${action}`);
  if (!res.ok || !res.data) {
    if (action === 'deeper' && res.data?.error === 'No enemy types available') {
      renderDungeonError(res.data.error);
      return;
    }
    if (res.data?.error) {
      const dungeonMessage = document.getElementById('dungeon-message');
      if (dungeonMessage) dungeonMessage.innerHTML = formatDungeonMessage(res.data.error);
    }
    return;
  }

  const dungeonState = res.data;
  const lootEl = document.getElementById('loot');
  applyDungeonCombatUpdate(dungeonState, {
    lootCounts: state.lootCounts,
    lootEl,
    setLastDungeonMessage: value => { state.lastDungeonMessage = value; }
  });

  if (dungeonState.victory) {
    state.dungeonActionMode = 'deeper';
    updateDungeonActionLabels({
      attackLabel: '⚔️GO DEEPER',
      runLabel: '🏠GO HOME',
    });
  } else {
    state.dungeonActionMode = 'run';
    updateDungeonActionLabels({
      attackLabel: '⚔️ATTACK',
      runLabel: '4/6🎲RUN AWAY',
    });
  }

  if (dungeonState.player_died) {
    state.activeCombat = null;
    showDungeonDefeatScreen({
      message: dungeonState.message || 'Defeat!\nYou have been defeated by the enemy!\nYou lost the loot from this dungeon run...',
      onExit: () => {
        resetDungeonLoot(state);
        navigateTo('/');
      }
    });
    return;
  }

  if (dungeonState.character) syncPlayerStatsInDom(dungeonState.character, document, { showCurrentHealth: true });
  if (dungeonState.combat) {
    state.activeCombat = dungeonState.combat;
    updateEnemyPanel(buildDungeonEnemy(dungeonState.combat));
  }
}

/** Go home after a victorious dungeon fight. */
async function handleDungeonHome() {
  if (!state.activeCombat?.id) return;
  const res = await fetchJson(`/combats/${state.activeCombat.id}/home`);
  if (!res.ok || !res.data) {
    if (res.data?.error) renderDungeonError(res.data.error);
    return;
  }

  const dungeonState = res.data;
  if (dungeonState.character) syncPlayerStatsInDom(dungeonState.character, document, { showCurrentHealth: true });

  state.activeCombat = null;
  state.dungeonActionMode = 'run';
  resetDungeonLoot(state);
  navigateTo('/');
}

/**
 * Send a run request and update the dungeon screen based on the result.
 * Handles escape attempts, victory, and continued combat.
 */
async function handleDungeonRun() {
  if (!state.activeCombat?.id) return;
  const res = await fetchJson(`/combats/${state.activeCombat.id}/run`);
  if (!res.ok || !res.data) {
    if (res.data?.error) {
      const dungeonMessage = document.getElementById('dungeon-message');
      if (dungeonMessage) dungeonMessage.innerHTML = formatDungeonMessage(res.data.error);
    }
    return;
  }

  const dungeonState = res.data;
  const dungeonMessage = document.getElementById('dungeon-message');
  if (dungeonMessage) {
    dungeonMessage.innerHTML = formatDungeonMessage(dungeonState.message || 'Action result');
  }

  if (dungeonState.character) {
    state.player = dungeonState.character;
    syncPlayerStatsInDom(dungeonState.character, document, { showCurrentHealth: true });
  }

  if (dungeonState.player_died) {
    state.activeCombat = null;
    showDungeonDefeatScreen({
      message: dungeonState.message || 'Defeat!\nYou have been defeated by the enemy!\nYou lost the loot from this dungeon run...',
      onExit: () => {
        resetDungeonLoot(state);
        navigateTo('/');
      }
    });
    return;
  }

  if (dungeonState.combat) {
    state.activeCombat = dungeonState.combat;
    updateEnemyPanel(buildDungeonEnemy(dungeonState.combat));
  }

  if (dungeonState.success) {
    state.activeCombat = null;
    setTimeout(async () => {
      resetDungeonLoot(state);
      navigateTo('/');
    }, 1500);
  }
}

/**
 * Render the dungeon screen and bind combat controls to live actions.
 * Fetches the latest encounter and wires up attack/run handlers.
 */
async function renderDungeon({ resetRunState = true } = {}) {
  if (resetRunState) resetDungeonLoot(state);
  state.dungeonActionMode = 'run';
  state.lastDungeonMessage = null;
  root.innerHTML = buildScreenShell({
    className: 'screen-shell--game',
    title: 'Dungeons & Databases',
    subtitle: 'Prepare for combat',
    sections: [{ id: 'dungeon-content', body: 'Loading...' }],
  });
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

  // The dungeon view always starts from the server-authoritative combat state.
  const combatResponse = await fetchJson('/combats', { method: 'POST' });
  const combatPayload = combatResponse.ok ? combatResponse.data : null;
  if (!combatResponse.ok || !combatPayload?.combat) {
    const errorMessage = combatPayload?.error || 'No enemy types available. Return to town and try again later.';
    content.innerHTML = buildScreenShell({
      className: 'screen-shell--game',
      title: 'Dungeons & Databases',
      subtitle: 'Prepare for combat',
      sections: [{
        className: 'screen-panel screen-panel--dark',
        body: `<div class="dungeon-message"><div class="dungeon-message-frame"><div class="dungeon-message-status dungeon-message-defeat-text">Defeat!</div><div class="dungeon-message-body"><div class="dungeon-message-line">${escapeHtml(errorMessage)}</div></div></div></div>`,
      }],
    });
    state.activeCombat = null;
    return;
  }
  const enemy = buildDungeonEnemy(combatPayload?.combat);
  state.activeCombat = combatPayload?.combat || null;
  if (combatPayload?.character) {
    state.player = combatPayload.character;
  }

  const preface = `A wild ${enemy?.name || 'creature'} appears! ${enemy?.description || ''}`;
  const messageToShow = state.lastDungeonMessage || preface;
  content.innerHTML = buildDungeonMarkup(enemy, messageToShow);

  renderPlayerStatsInto(document.getElementById('player-stats-container'), state.player, { showCurrentHealth: true });
  const lootEl = document.getElementById('loot');
  if (lootEl) {
    renderLootPanel(lootEl, state.lootCounts);
  }
  state.lastDungeonMessage = null;
  updateEnemyPanel(enemy);

  document.getElementById('attack').addEventListener('click', event => {
    event.preventDefault();
    handleDungeonAttack();
  });
  document.getElementById('run').addEventListener('click', event => {
    event.preventDefault();
    if (event.currentTarget?.dataset.action === 'home') {
      handleDungeonHome();
      return;
    }
    handleDungeonRun();
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