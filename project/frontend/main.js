import { fetchJson } from './api.js';
import { makeIcon, getItemType, formatStats } from './helpers.js';
import { renderPlayerStatsInto } from './components/player.js';
import { renderEquipPanel as renderEquipPanelImpl } from './components/equip.js';
import { renderInventoryGrid as renderInventoryGridImpl } from './components/inventory.js';
import { showHome } from './screens/home.js';
import { showDungeon } from './screens/dungeon.js';
import { showDefeat } from './screens/defeat.js';
// action button helpers are used via page.js; no direct imports needed here
import { setupActionButtons, setupRubbishBin } from './page.js';

const root = document.getElementById('root');

let player = null;
let inventory = [];
let equipped = [];
let allItems = [];
let currentDrag = null; // { itemId, itemType, from, slot }
let lastDungeonMessage = null;
let lootCounts = {}; // cumulative loot counts while in session
let reforgeState = { baseId: null, count: 0 };

function updateSlotHighlights() {
  document.querySelectorAll('.equip-slot').forEach(slotEl => {
    slotEl.classList.remove('slot-allowed', 'slot-denied');
    if (!currentDrag) return;
    const slotType = slotEl.getAttribute('data-slot-type') || 'misc';
    const itype = currentDrag.itemType || 'misc';
    const allowed = (slotType === 'misc') ? (['weapon','armor','shield'].indexOf(itype) === -1) : (slotType === itype);
    if (allowed) slotEl.classList.add('slot-allowed'); else slotEl.classList.add('slot-denied');
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
    inventory, reforgeState,
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
// expose renderers for screen modules
window.app = window.app || {};
window.app.renderHome = renderHome;

async function loadStateAndRenderPartial() {
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
  root.innerHTML = `<div class="game-container"><h1>Dungeons and Databases</h1><div id="main-content"></div></div>`;
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div style="display:flex;gap:20;align-items:stretch;">
      <div id="player-stats-container" style="flex:1;min-width:260px;display:flex;flex-direction:column;box-sizing:border-box">
        <div id="player-stats" style=""></div>
          <div id="player-stats-actions"></div>
      </div>
      <div id="equip-panel" style="flex:1;min-width:260px"></div>
    </div>
    <h3 style="margin-top:20px;color:#ffd700">Inventory</h3>
    <div id="inventory-grid" class="inventory-grid" style="margin-top:10px"></div>
    <div id="rubbish-bin" class="rubbish-bin">🗑️ Drop items here to destroy</div>
    <div style="margin-bottom:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:20px">
      <button class="dungeon-button" id="enter-dungeon">Enter the Dungeon</button>
    </div>
  `;

  document.getElementById('enter-dungeon').addEventListener('click', () => navigateTo('/dungeon'));

  // clear any dungeon loot from previous runs when returning home
  lootCounts = {};
  await loadStateAndRenderPartial();
  // Heal player to full when returning to home: compute base max from level + bonuses
  try {
    const lvl = (player && player.level) ? player.level : 1;
    const baseMax = 100 + (Math.max(0, lvl - 1) * 10);
    const bonus = (player && player.bonus_health) ? player.bonus_health : 0;
    const fullHealth = baseMax + bonus;
    await fetchJson('/player', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ health: fullHealth }) });
    // re-render stats after heal
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
async function renderDungeon() {
  // reset loot counts for a fresh run when entering the dungeon
  lootCounts = {};
  root.innerHTML = `<div class="game-container"><h1>The Dungeon</h1><div id="dungeon-content">Loading...</div></div>`;
  const content = document.getElementById('dungeon-content');

  const [pRes, encRes] = await Promise.all([fetchJson('/player'), fetchJson('/dungeon/encounter')]);
  player = pRes.ok ? pRes.data : player;
  const enemy = encRes.ok ? encRes.data : { name: '', health: 0, max_health: 0, damage: 0, description: '' };

  const preface = `A wild ${enemy.name || 'creature'} appears! ${enemy.description || ''}`;
  const messageToShow = lastDungeonMessage || preface;
  content.innerHTML = `
    <div id="dungeon-wrap" style="display:flex;flex-direction:column;gap:12px;">
      <div id="dungeon-top" style="padding:0;margin:0">
        <div style="margin-top:20px;font-size:1.2em;min-height:60px;padding:8px">
          <p id="dungeon-message">${messageToShow}</p>
        </div>

        <div style="display:flex;gap:20;justify-content:center;flex-wrap:wrap;align-items:stretch;margin-top:12px;padding:8px">
          <div id="player-stats-container" style="flex:1;min-width:250px;max-width:400px"></div>
          <div class="player-stats" style="flex:1;min-width:250px;max-width:400px;border-color:#ff6b6b">
            <h2 id="enemy-name" style="color:#ff6b6b">Enemy: ${enemy.name || 'None'}</h2>
            <div class="stat"><span class="stat-label">Level:</span><span id="enemy-level" class="stat-value">${enemy.level || ''}</span></div>
            <div class="stat"><span class="stat-label">Health:</span><span id="enemy-health" class="stat-value">${enemy.health} / ${enemy.max_health} HP</span></div>
            <div class="stat"><span class="stat-label">Damage:</span><span id="enemy-damage" class="stat-value">${enemy.damage}</span></div>
              </div>
        </div>
      </div>

      <div id="dungeon-actions" style="margin-top:8px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
        <button type="button" class="dungeon-button" id="attack">Attack</button>
        <button type="button" class="dungeon-button" id="run" style="background:linear-gradient(135deg,#ff9f1c 0%,#ffb700 100%)">Run Away</button>
        <button type="button" class="dungeon-button" id="back">Back to Home</button>
      </div>

      <div id="loot" style="margin-top:6px;padding:8px"></div>
    </div>
  `;

  // render player stats into dungeon layout
  renderPlayerStatsInto(document.getElementById('player-stats-container'), player);

  // clear preserved message after rendering so future new-encounter renders use preface
  lastDungeonMessage = null;

  document.getElementById('attack').addEventListener('click', async (ev) => {
    ev.preventDefault();
    const res = await fetchJson('/dungeon/attack', { method: 'POST' });
    if (res.ok && res.data) {
      const d = res.data;
      lastDungeonMessage = d.message || 'You attacked the monster!';
      document.getElementById('dungeon-message').textContent = lastDungeonMessage;
      const lootEl = document.getElementById('loot');
          if (d.items_dropped && d.items_dropped.length) {
            // accumulate counts
            d.items_dropped.forEach(it => {
              const n = it.name || 'Unknown';
              lootCounts[n] = (lootCounts[n] || 0) + 1;
            });
            // render cumulative list
            const lines = Object.keys(lootCounts).map(name => `${name}${lootCounts[name] > 1 ? ' x' + lootCounts[name] : ''}`);
            lootEl.innerHTML = `<div style="margin-top:10px;padding:10px;background:#2d3436;border-left:4px solid #fdcb6e;border-radius:4px"><strong style="color:#fdcb6e">🎁 Loot obtained:</strong><p>${lines.join(', ')}</p></div>`;
          }
      if (d.player_died) {
        await showDefeat({ message: d.message || 'You were defeated', lootCounts, onExit: () => { lootCounts = {}; navigateTo('/'); } });
        return;
      } else {
        await loadStateAndRenderPartial();
        // Update player panel in-place if server returned updated player
        if (d.player) updatePlayerPanel(d.player);
        // Update enemy panel in-place from response (no full re-render)
        if (d.enemy) updateEnemyPanel(d.enemy);
      }
    }
  });

  document.getElementById('run').addEventListener('click', async (ev) => {
    ev.preventDefault();
    const res = await fetchJson('/dungeon/run', { method: 'POST' });
    if (res.ok && res.data) {
      const d = res.data;
      document.getElementById('dungeon-message').textContent = d.message || 'Action result';
      if (d.player_died) {
        await showDefeat({ message: d.message || 'You were defeated', lootCounts, onExit: () => { lootCounts = {}; navigateTo('/'); } });
        return;
      } else if (d.success) {
        setTimeout(() => navigateTo('/'), 1500);
      } else {
        setTimeout(() => renderDungeon(), 500);
      }
    }
  });

  document.getElementById('back').addEventListener('click', (ev) => { ev.preventDefault(); navigateTo('/'); });
}

// expose dungeon renderer as well
window.app = window.app || {};
window.app.renderDungeon = renderDungeon;

/* --- Router --- */
function navigateTo(path) { if (path === '/') location.hash = '#/'; else location.hash = `#${path}`; }

function route() { const hash = location.hash.replace('#', '') || '/'; if (hash === '/' || hash === '') return showHome(); else if (hash === '/dungeon') return showDungeon(); else return showHome(); }

window.addEventListener('hashchange', route);
window.addEventListener('load', route);
