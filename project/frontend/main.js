import { fetchJson } from './api.js';
import { makeIcon, getItemType, formatDungeonMessage, formatStats, isSlotCompatible } from './helpers.js';
import { renderPlayerStatsInto } from './components/player.js';
import { renderEquipPanel as renderEquipPanelImpl } from './components/equip.js';
import { renderInventoryGrid as renderInventoryGridImpl } from './components/inventory.js';
import { showHome } from './screens/home.js';
import { showDungeon } from './screens/dungeon.js';
import { buildDungeonMarkup, applyDungeonCombatUpdate, showDungeonDefeatScreen } from './screens/dungeon-runtime.js';
// action button helpers are used via page.js; no direct imports needed here
import { setupActionButtons, setupRubbishBin } from './page.js';

const root = document.getElementById('root');

// Shared app state stays in memory so each screen can re-render without rebuilding the data model.
let player = null;
let inventory = [];
let equipped = [];
let allItems = [];
let currentDrag = null; // { itemId, itemType, from, slot }
let lastDungeonMessage = null;
let lootCounts = {}; // cumulative loot counts while in session
let dungeonLoot = []; // temporary dungeon-run loot that is only banked on successful exit

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

  const countsById = new Map();
  dungeonLoot.forEach(item => {
    if (!item || item.id === undefined || item.id === null) return;
    const current = countsById.get(item.id) || { item, quantity: 0 };
    current.quantity += 1;
    countsById.set(item.id, current);
  });

  for (const { item, quantity } of countsById.values()) {
    for (let i = 0; i < quantity; i += 1) {
      await fetchJson(`/inventory/item/${item.id}`, { method: 'POST' });
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
  if (ph) ph.textContent = `${p.health} HP`;
  if (pd) pd.textContent = `${p.damage}`;
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

function renderInventoryGrid() {
  return renderInventoryGridImpl({
    inventory,
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
  const [pRes, invRes, eqRes, allRes] = await Promise.all([
    fetchJson('/player'), fetchJson('/inventory'), fetchJson('/inventory/equipped'), fetchJson('/inventory/items')
  ]);
  if (pRes.ok) player = pRes.data;
  inventory = invRes.ok ? invRes.data : [];
  equipped = eqRes.ok ? eqRes.data : [];
  allItems = allRes.ok ? allRes.data : [];

  // update parts
  const mainContent = document.getElementById('main-content');
  if (!mainContent) return;
  renderPlayerStatsInto(document.getElementById('player-stats'), player);
  renderEquipPanel();
  renderInventoryGrid();
}

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
    </div>
  `;

  document.getElementById('enter-dungeon').addEventListener('click', () => navigateTo('/dungeon'));

  // clear any dungeon loot from previous runs when returning home
  resetDungeonLoot();
  await loadStateAndRenderPartial();
  // Returning home restores the player to full health based on level and gear bonuses.
  try {
    const lvl = (player && player.level) ? player.level : 1;
    const baseMax = 100 + (Math.max(0, lvl - 1) * 10);
    const bonus = (player && player.bonus_health) ? player.bonus_health : 0;
    const fullHealth = baseMax + bonus;
    await fetchJson('/player', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ health: fullHealth }) });
    const refreshedPlayer = await fetchJson('/player');
    if (refreshedPlayer.ok) player = refreshedPlayer.data;
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
    getItemType
  });

  const bin = document.getElementById('rubbish-bin');
  setupRubbishBin(bin, {
    fetchJson,
    loadStateAndRenderPartial,
    getCurrentDrag: () => currentDrag,
    setCurrentDrag: v => { currentDrag = v; },
    updateSlotHighlights
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

function route() { const hash = location.hash.replace('#', '') || '/'; if (hash === '/' || hash === '') return showHome(); else if (hash === '/dungeon') return showDungeon(); else return showHome(); }

// Keep the SPA shell in sync with the URL hash.
window.addEventListener('hashchange', route);
window.addEventListener('load', route);
