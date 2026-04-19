import { fetchJson } from './api.js';
import { makeIcon, getItemType, formatDungeonMessage, formatStats, isSlotCompatible } from './helpers.js';
import { renderPlayerStatsInto } from './components/player.js';
import { renderEquipPanel as renderEquipPanelImpl } from './components/equip.js';
import { renderInventoryGrid as renderInventoryGridImpl } from './components/inventory.js';
import { showHome } from './screens/home.js';
import { showDungeon } from './screens/dungeon.js';
import { buildDungeonMarkup, applyDungeonCombatUpdate, showDungeonDefeatScreen } from './screens/dungeon-runtime.js';
import { showLogin } from './screens/login.js';
import { showCharacterSelect } from './screens/character-select.js';
// action button helpers are used via page.js; no direct imports needed here
import { setupActionButtons, setupRubbishBin } from './page.js';

const root = document.getElementById('root');

// Shared app state stays in memory so each screen can re-render without rebuilding the data model.
let currentUser = null;
let characters = [];
let player = null;
let inventory = [];
let equipped = [];
let allItems = [];
let currentDrag = null; // { itemId, itemType, from, slot }
let lastDungeonMessage = null;
let lootCounts = {}; // cumulative loot counts while in session
let dungeonLoot = []; // temporary dungeon-run loot that is only banked on successful exit

function getCharacterId() {
  return player && player.id ? player.id : null;
}

function getCharacterInventoryPath(suffix = '') {
  const characterId = getCharacterId();
  if (!characterId) return null;
  return `/characters/${characterId}/inventory/${suffix}`;
}

function getReforgeAllPath() {
  const characterId = getCharacterId();
  if (!characterId) return null;
  return `/forge/reforge_all/${characterId}`;
}

function getFullHealthForPlayer(playerState) {
  if (!playerState) return null;
  const level = playerState.level || 1;
  const baseMax = 100 + (Math.max(0, level - 1) * 10);
  return baseMax + (playerState.bonus_health || 0);
}

async function syncPlayerHealthToFull() {
  const fullHealth = getFullHealthForPlayer(player);
  if (fullHealth === null) return;

  await fetchJson('/player', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ health: fullHealth })
  });

  const refreshedPlayer = await fetchJson('/player/full');
  if (refreshedPlayer.ok && refreshedPlayer.data) {
    player = refreshedPlayer.data;
    inventory = Array.isArray(player.inventory) ? player.inventory : inventory;
    equipped = Array.isArray(player.equipped) ? player.equipped : equipped;
    allItems = [...inventory, ...equipped];
    const statsContainer = document.getElementById('player-stats');
    if (statsContainer) {
      renderPlayerStatsInto(statsContainer, player);
    }
  }
}

function resetDungeonLoot() {
  lootCounts = {};
  dungeonLoot = [];
}

function recordDungeonLoot(itemsDropped) {
  (itemsDropped || []).forEach(item => {
    if (!item) return;
    dungeonLoot.push(item);
  });
}

async function bankDungeonLoot() {
  if (!dungeonLoot.length) return;
  const inventoryPath = getCharacterInventoryPath();
  if (!inventoryPath) return;

  const countsById = new Map();
  dungeonLoot.forEach(item => {
    if (!item || item.id === undefined || item.id === null) return;
    const current = countsById.get(item.id) || { item, quantity: 0 };
    current.quantity += 1;
    countsById.set(item.id, current);
  });

  for (const { item, quantity } of countsById.values()) {
    for (let i = 0; i < quantity; i += 1) {
      await fetchJson(`${inventoryPath}${item.id}`, { method: 'POST' });
    }
  }
}

function updateSlotHighlights() {
  document.querySelectorAll('.equip-slot').forEach(slotEl => {
    slotEl.classList.remove('slot-allowed', 'slot-denied');
    if (!currentDrag) return;
    const slotType = slotEl.getAttribute('data-slot-type') || 'misc';
    const itype = currentDrag.itemType || 'misc';
    if (isSlotCompatible(slotType, itype)) slotEl.classList.add('slot-allowed'); else slotEl.classList.add('slot-denied');
  });
}

function updatePlayerPanel(p) {
  if (!p) return;
  const ph = document.getElementById('player-health');
  const pd = document.getElementById('player-damage');
  const pl = document.getElementById('player-level');
  const pbh = document.getElementById('player-bonus-health');
  const pbd = document.getElementById('player-bonus-damage');
  const level = p.level || 1;
  const maxHealth = (100 + (Math.max(0, level - 1) * 10)) + (p.bonus_health || 0);
  const totalDamage = (p.damage || 0) + (p.bonus_damage || 0);
  if (ph) ph.textContent = `${p.health} / ${maxHealth} HP`;
  if (pd) pd.textContent = `${totalDamage}`;
  if (pl) pl.textContent = `${p.level}`;
  if (pbh) pbh.textContent = `+${p.bonus_health}`;
  if (pbd) pbd.textContent = `+${p.bonus_damage}`;
}

function updateEnemyPanel(en) {
  if (!en) return;
  const enName = document.getElementById('enemy-name');
  const enLevel = document.getElementById('enemy-level');
  const enHealth = document.getElementById('enemy-health');
  const enDamage = document.getElementById('enemy-damage');
  if (enName) enName.textContent = `Enemy: ${en.name || 'None'}`;
  if (enLevel) enLevel.textContent = `${en.level || ''}`;
  if (enHealth) enHealth.textContent = `${en.health} / ${en.max_health} HP`;
  if (enDamage) enDamage.textContent = `${en.damage}`;
}

function renderEquipPanel() {
  return renderEquipPanelImpl({
    equipped, inventory, allItems,
    getCharacterId,
    getCurrentDrag: () => currentDrag,
    setCurrentDrag: v => { currentDrag = v; },
    updateSlotHighlights,
    fetchJson,
    loadStateAndRenderPartial,
    syncPlayerHealthToFull,
    getItemType,
    makeIcon,
    formatStats
  });
}

function renderInventoryGrid() {
  return renderInventoryGridImpl({
    inventory,
    getCharacterId,
    getCurrentDrag: () => currentDrag,
    setCurrentDrag: v => { currentDrag = v; },
    updateSlotHighlights,
    fetchJson,
    loadStateAndRenderPartial,
    getItemType,
    makeIcon,
    formatStats
  });
}

async function handleDungeonAttack() {
  const res = await fetchJson('/dungeon/attack', { method: 'POST' });
  if (!res.ok || !res.data) return;

  const d = res.data;
  const lootEl = document.getElementById('loot');
  applyDungeonCombatUpdate(d, {
    lootCounts,
    onLootDropped: recordDungeonLoot,
    lootEl,
    setLastDungeonMessage: v => { lastDungeonMessage = v; }
  });

  if (d.player_died) {
    await showDungeonDefeatScreen({
      message: d.message || 'You were defeated and lost the loot from this dungeon run.',
      lootCounts,
      onExit: () => {
        resetDungeonLoot();
        navigateTo('/');
      }
    });
    return;
  }

  await loadStateAndRenderPartial();
  if (d.player) updatePlayerPanel(d.player);
  if (d.enemy) updateEnemyPanel(d.enemy);
}

async function handleDungeonRun() {
  const res = await fetchJson('/dungeon/run', { method: 'POST' });
  if (!res.ok || !res.data) return;

  const d = res.data;
  const dungeonMessage = document.getElementById('dungeon-message');
  if (dungeonMessage) dungeonMessage.innerHTML = formatDungeonMessage(d.message || 'Action result');

  if (d.player_died) {
    await showDungeonDefeatScreen({
      message: d.message || 'You were defeated and lost the loot from this dungeon run.',
      lootCounts,
      onExit: () => {
        resetDungeonLoot();
        navigateTo('/');
      }
    });
    return;
  }

  if (d.success) {
    setTimeout(async () => {
      try {
        await bankDungeonLoot();
      } catch (err) {
        console.error('Banking dungeon loot failed', err);
      } finally {
        resetDungeonLoot();
        navigateTo('/');
      }
    }, 1500);
  } else {
    setTimeout(() => renderDungeon({ resetRunState: false }), 500);
  }
}
// expose renderers for screen modules
window.app = window.app || {};
window.app.renderHome = renderHome;

async function loadStateAndRenderPartial() {
  // Pull the latest server state before redrawing the visible panels.
  const pRes = await fetchJson('/player/full');
  if (pRes.ok && pRes.data) {
    player = pRes.data;
    inventory = Array.isArray(pRes.data.inventory) ? pRes.data.inventory : [];
    equipped = Array.isArray(pRes.data.equipped) ? pRes.data.equipped : [];
    allItems = [...inventory, ...equipped];
  }

  // update parts
  const mainContent = document.getElementById('main-content');
  if (!mainContent) return;
  renderPlayerStatsInto(document.getElementById('player-stats'), player);
  renderEquipPanel();
  renderInventoryGrid();
}

/* --- Login Screen --- */
async function renderLogin() {
  root.innerHTML = `
    <div class="game-container" style="display: flex; justify-content: center; align-items: center; min-height: 100vh;">
      <div style="width: 100%; max-width: 400px; padding: 20px;">
        <h1 style="text-align: center; margin-bottom: 30px;">Dungeons & Databases</h1>
        <div id="login-container">
          <div style="margin-bottom: 20px;">
            <label for="username" style="display: block; margin-bottom: 5px;">Username:</label>
            <input type="text" id="username" placeholder="Enter username" style="width: 100%; padding: 8px; box-sizing: border-box;">
          </div>
          <div style="margin-bottom: 20px;">
            <label for="password" style="display: block; margin-bottom: 5px;">Password:</label>
            <input type="password" id="password" placeholder="Enter password" style="width: 100%; padding: 8px; box-sizing: border-box;">
          </div>
          <div id="login-message" style="margin-bottom: 15px; min-height: 20px; color: red; text-align: center;"></div>
          <div style="display: flex; gap: 10px;">
            <button id="signin-btn" style="flex: 1; padding: 10px; cursor: pointer;">Sign In</button>
            <button id="signup-btn" style="flex: 1; padding: 10px; cursor: pointer;">Sign Up</button>
          </div>
        </div>
      </div>
    </div>
  `;

  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const messageEl = document.getElementById('login-message');

  document.getElementById('signin-btn').addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    if (!username || !password) {
      messageEl.textContent = 'Username and password required';
      return;
    }

    const res = await fetchJson('/login/signin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok && res.data.user) {
      currentUser = res.data.user;
      navigateTo('/character-select');
    } else {
      messageEl.textContent = res.data?.message || 'Sign in failed';
    }
  });

  document.getElementById('signup-btn').addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    if (!username || !password) {
      messageEl.textContent = 'Username and password required';
      return;
    }

    const res = await fetchJson('/login/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok && res.data.user) {
      currentUser = res.data.user;
      navigateTo('/character-select');
    } else {
      messageEl.textContent = res.data?.message || 'Sign up failed';
    }
  });
}

window.app = window.app || {};
window.app.renderLogin = renderLogin;

/* --- Character Select Screen --- */
async function renderCharacterSelect() {
  root.innerHTML = `<div class="game-container" style="display: flex; justify-content: center; align-items: center; min-height: 100vh;"><div style="width: 100%; max-width: 600px; padding: 20px;" id="char-select-content">Loading...</div></div>`;
  const content = document.getElementById('char-select-content');

  const res = await fetchJson('/characters/');
  characters = res.ok ? res.data : [];

  content.innerHTML = `
    <h1 style="text-align: center; margin-bottom: 30px;">Select or Create a Character</h1>
    <div id="character-list" style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px;"></div>
    <button id="create-char-btn" style="width: 100%; padding: 12px; cursor: pointer; font-size: 16px;">Create New Character</button>
    <button id="logout-btn" style="width: 100%; padding: 10px; cursor: pointer; margin-top: 10px; background-color: #666;">Logout</button>
  `;

  const charList = document.getElementById('character-list');
  if (characters.length === 0) {
    charList.innerHTML = '<p style="text-align: center; color: #999;">No characters yet. Create one to start playing!</p>';
  } else {
    characters.forEach(char => {
      const charEl = document.createElement('button');
      charEl.style.cssText = 'padding: 15px; text-align: left; cursor: pointer; border: 1px solid #ccc; background-color: #f5f5f5; border-radius: 4px;';
      charEl.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 5px;">${char.name}</div>
        <div style="font-size: 12px; color: #666;">Level ${char.level} | ${char.health} HP</div>
      `;
      charEl.addEventListener('click', async () => {
        const selectRes = await fetchJson(`/characters/${char.id}/select`, {
          method: 'POST'
        });
        if (selectRes.ok && selectRes.data.player) {
          player = selectRes.data.player;
          inventory = [];
          equipped = [];
          allItems = [];
          navigateTo('/');
        }
      });
      charList.appendChild(charEl);
    });
  }

  document.getElementById('create-char-btn').addEventListener('click', async () => {
    const charName = prompt('Enter character name:') || 'Hero';
    const createRes = await fetchJson('/characters/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: charName })
    });
    if (createRes.ok && createRes.data) {
      player = createRes.data;
      inventory = [];
      equipped = [];
      allItems = [];
      navigateTo('/');
    }
  });

  document.getElementById('logout-btn').addEventListener('click', async () => {
    await fetchJson('/login/signout', { method: 'POST' });
    currentUser = null;
    player = null;
    characters = [];
    navigateTo('/login');
  });
}

window.app = window.app || {};
window.app.renderCharacterSelect = renderCharacterSelect;

async function renderHome() {
  // Home is the management hub: stats, equipment, inventory, and the entry point to the dungeon.
  root.innerHTML = `<div class="game-container"><div id="main-content"></div></div>`;
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div style="display:flex;gap:20;align-items:stretch;">
      <div id="player-stats-container" style="flex:1;min-width:260px;display:flex;flex-direction:column;box-sizing:border-box;height:100%;min-height:0">
        <div id="player-stats" style=""></div>
          <div id="player-stats-actions"></div>
      </div>
      <div id="equip-panel" style="flex:1;min-width:260px"></div>
    </div>
    <div class="inventory-scroll-box">
      <div id="inventory-grid" class="inventory-grid"></div>
    </div>
    <div id="rubbish-bin" class="rubbish-bin">🗑️ Drop items here to destroy</div>
    <div style="margin-top:20px;display:flex;justify-content:center;flex-wrap:wrap;gap:10px;">
      <button class="dungeon-button" id="enter-dungeon">Enter the Dungeon</button>
      <button class="dungeon-button" id="select-character-btn" style="background-color: #666;">Change Character</button>
      <button class="dungeon-button" id="logout-btn" style="background-color: #333;">Logout</button>
    </div>
  `;

  document.getElementById('enter-dungeon').addEventListener('click', () => navigateTo('/dungeon'));
  
  document.getElementById('select-character-btn').addEventListener('click', () => navigateTo('/character-select'));
  
  document.getElementById('logout-btn').addEventListener('click', async () => {
    await fetchJson('/login/signout', { method: 'POST' });
    currentUser = null;
    player = null;
    characters = [];
    navigateTo('/login');
  });

  // clear any dungeon loot from previous runs when returning home
  resetDungeonLoot();
  await loadStateAndRenderPartial();
  // Returning home restores the player to full health based on level and gear bonuses.
  try {
    await syncPlayerHealthToFull();
    renderPlayerStatsInto(document.getElementById('player-stats'), player);
  } catch (e) {
    console.warn('Heal on home failed', e);
  }

  // wire up action buttons and rubbish bin via helpers to keep main concise
  const actionsContainer = document.getElementById('player-stats-actions');
  setupActionButtons(actionsContainer, {
    fetchJson,
    loadStateAndRenderPartial,
    getEquipped: () => equipped,
    getInventory: () => inventory,
    getItemType,
    getCharacterId,
    syncPlayerHealthToFull
  });

  const bin = document.getElementById('rubbish-bin');
  setupRubbishBin(bin, {
    fetchJson,
    loadStateAndRenderPartial,
    getCurrentDrag: () => currentDrag,
    setCurrentDrag: v => { currentDrag = v; },
    updateSlotHighlights,
    getCharacterId,
    syncPlayerHealthToFull
  });
}

/* --- Dungeon view remains mostly unchanged but uses player updates from API --- */
async function renderDungeon({ resetRunState = true } = {}) {
  // Reset transient combat state only when starting a fresh dungeon screen.
  if (resetRunState) resetDungeonLoot();
  lastDungeonMessage = null;
  root.innerHTML = `<div class="game-container"><div id="dungeon-content">Loading...</div></div>`;
  const content = document.getElementById('dungeon-content');

  const [pRes, encRes] = await Promise.all([fetchJson('/player'), fetchJson('/dungeon/encounter')]);
  player = pRes.ok ? pRes.data : player;
  const enemy = encRes.ok ? encRes.data : { name: '', health: 0, max_health: 0, damage: 0, description: '' };

  const preface = `A wild ${enemy.name || 'creature'} appears! ${enemy.description || ''}`;
  const messageToShow = lastDungeonMessage || preface;
  content.innerHTML = buildDungeonMarkup(enemy, messageToShow);

  // render player stats into dungeon layout
  renderPlayerStatsInto(document.getElementById('player-stats-container'), player);

  // clear preserved message after rendering so future new-encounter renders use preface
  lastDungeonMessage = null;

  document.getElementById('attack').addEventListener('click', ev => { ev.preventDefault(); handleDungeonAttack(); });

  document.getElementById('run').addEventListener('click', ev => { ev.preventDefault(); handleDungeonRun(); });

  document.getElementById('back').addEventListener('click', (ev) => {
    ev.preventDefault();
    resetDungeonLoot();
    navigateTo('/');
  });
}

// expose dungeon renderer as well
window.app = window.app || {};
window.app.renderDungeon = renderDungeon;

/* --- Router --- */
function navigateTo(path) { if (path === '/') location.hash = '#/'; else location.hash = `#${path}`; }

async function route() { 
  const hash = location.hash.replace('#', '') || '/'; 
  
  // Check authentication status if needed
  if (!currentUser && hash !== '/login') {
    // Try to load current user from server
    const res = await fetchJson('/login/me');
    if (res.ok && res.data && res.data.user) {
      currentUser = res.data.user;
    } else {
      // Not logged in, redirect to login
      location.hash = '#/login';
      return;
    }
  }
  
  if (hash === '/login') return showLogin();
  else if (hash === '/character-select') return showCharacterSelect();
  else if (hash === '/' || hash === '') return (player ? showHome() : showCharacterSelect());
  else if (hash === '/dungeon') return showDungeon();
  else return showHome();
}

// Keep the SPA shell in sync with the URL hash.
window.addEventListener('hashchange', route);
window.addEventListener('load', route);
