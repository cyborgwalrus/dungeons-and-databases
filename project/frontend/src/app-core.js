import { fetchJson, clearAuthToken, setAuthToken } from './api.js';
import { escapeHtml, makeIcon, getItemType, getItemDisplayName, formatDungeonMessage, formatStats } from './helpers.js';
import { renderPlayerStatsInto } from './components/player.js';
import { renderEquipPanel as renderEquipPanelImpl } from './components/equip.js';
import { renderInventoryGrid as renderInventoryGridImpl } from './components/inventory.js';
import { buildDungeonMarkup, applyDungeonCombatUpdate, showDungeonDefeatScreen } from './screens/dungeon-runtime.js';
import { state, getCharacterId } from './app-state.js';

const root = document.getElementById('root');

function syncPlayerSnapshot(playerData) {
  state.player = playerData;
}

async function syncPlayerHealthToFull() {
  const characterId = getCharacterId();
  if (!characterId) return;

  const refreshedPlayer = await fetchJson(`/characters/${characterId}/full_heal`, {
    method: 'POST'
  });
  if (refreshedPlayer.ok && refreshedPlayer.data) {
    syncPlayerSnapshot(refreshedPlayer.data);
    const statsContainer = document.getElementById('player-stats');
    if (statsContainer) {
      renderPlayerStatsInto(statsContainer, state.player);
    }
  }
}

function resetDungeonLoot() {
  state.lootCounts = {};
}

async function clearUnequippedInventory() {
  const userId = state.currentUser?.id || state.player?.user_id;
  if (!userId) return;

  await fetchJson(`/users/${userId}/inventory`, { method: 'DELETE' });
  await loadStateAndRenderPartial();
  await syncPlayerHealthToFull();
}

function updatePlayerPanel(player) {
  if (!player) return;
  const ph = document.getElementById('player-health');
  const pd = document.getElementById('player-damage');
  const pl = document.getElementById('player-level');
  const pxp = document.getElementById('player-xp');
  const pbh = document.getElementById('player-bonus-health');
  const pbd = document.getElementById('player-bonus-damage');
  const level = player.level || 1;
  const maxHealth = player.max_health ?? ((100 + (Math.max(0, level - 1) * 10)) + (player.bonus_health || 0));
  const totalDamage = (player.damage || 0) + (player.bonus_damage || 0);
  const experience = player.experience || 0;
  const experienceToNextLevel = player.experience_to_next_level || (100 + (Math.max(0, level - 1) * 50));
  if (ph) ph.textContent = `${player.health} / ${maxHealth} HP`;
  if (pd) pd.textContent = `${totalDamage}`;
  if (pl) pl.textContent = `${player.level}`;
  if (pxp) pxp.textContent = `${experience} / ${experienceToNextLevel}`;
  if (pbh) pbh.textContent = `+${player.bonus_health}`;
  if (pbd) pbd.textContent = `+${player.bonus_damage}`;
}

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

function renderEquipPanel() {
  const equipped = Array.isArray(state.player?.equipped) ? state.player.equipped : [];
  const inventory = Array.isArray(state.player?.inventory) ? state.player.inventory : [];
  return renderEquipPanelImpl({
    equipped,
    inventory,
    allItems: [...inventory, ...equipped],
    fetchJson,
    loadStateAndRenderPartial,
    syncPlayerHealthToFull,
    getItemType,
    makeIcon,
    formatStats,
    getItemDisplayName,
  });
}

function renderInventoryGrid() {
  const inventory = Array.isArray(state.player?.inventory) ? state.player.inventory : [];
  const equipped = Array.isArray(state.player?.equipped) ? state.player.equipped : [];
  return renderInventoryGridImpl({
    inventory,
    equipped,
    fetchJson,
    loadStateAndRenderPartial,
    syncPlayerHealthToFull,
    getItemType,
    makeIcon,
    formatStats,
    getItemDisplayName,
  });
}

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
        resetDungeonLoot();
        navigateTo('/');
      }
    });
    return;
  }

  await loadStateAndRenderPartial();
  if (dungeonState.character) updatePlayerPanel(dungeonState.character);
  if (dungeonState.enemy) updateEnemyPanel(dungeonState.enemy);
}

async function handleDungeonRun() {
  const res = await fetchJson('/dungeon/run', { method: 'POST' });
  if (!res.ok || !res.data) return;

  const dungeonState = res.data;
  const dungeonMessage = document.getElementById('dungeon-message');
  if (dungeonMessage) dungeonMessage.innerHTML = formatDungeonMessage(dungeonState.message || 'Action result');

  if (dungeonState.player_died) {
    await showDungeonDefeatScreen({
      message: dungeonState.message || 'You were defeated and lost the loot from this dungeon run.',
      lootCounts: state.lootCounts,
      onExit: () => {
        resetDungeonLoot();
        navigateTo('/');
      }
    });
    return;
  }

  if (dungeonState.success) {
    setTimeout(async () => {
      resetDungeonLoot();
      navigateTo('/');
    }, 1500);
  } else {
    setTimeout(() => renderDungeon({ resetRunState: false }), 500);
  }
}

async function loadStateAndRenderPartial() {
  const characterId = getCharacterId();
  if (!characterId) return;

  const playerResponse = await fetchJson(`/characters/${characterId}`);
  if (playerResponse.ok && playerResponse.data) {
    syncPlayerSnapshot(playerResponse.data);
  }

  const mainContent = document.getElementById('main-content');
  if (!mainContent) return;
  renderPlayerStatsInto(document.getElementById('player-stats'), state.player);
  renderEquipPanel();
  renderInventoryGrid();
}

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
      if (res.data.token) setAuthToken(res.data.token);
      state.currentUser = res.data.user;
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
      if (res.data.token) setAuthToken(res.data.token);
      state.currentUser = res.data.user;
      navigateTo('/character-select');
    } else {
      messageEl.textContent = res.data?.message || 'Sign up failed';
    }
  });
}

async function renderCharacterSelect() {
  root.innerHTML = `<div class="game-container" style="display: flex; justify-content: center; align-items: center; min-height: 100vh;"><div style="width: 100%; max-width: 600px; padding: 20px;" id="char-select-content">Loading...</div></div>`;
  const content = document.getElementById('char-select-content');
  if (!state.currentUser) {
    navigateTo('/login');
    return;
  }

  const res = await fetchJson('/characters');
  state.characters = res.ok ? res.data : [];

  content.innerHTML = `
    <h1 style="text-align: center; margin-bottom: 30px;">Select or Create a Character</h1>
    <div id="character-list" style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px;"></div>
    <div style="margin-bottom: 10px;">
      <input type="text" id="create-char-name" placeholder="Enter character name" style="width: 100%; padding: 12px; box-sizing: border-box;">
    </div>
    <button id="create-char-btn" style="width: 100%; padding: 12px; cursor: pointer; font-size: 16px;">Create New Character</button>
    <button id="logout-btn" style="width: 100%; padding: 10px; cursor: pointer; margin-top: 10px; background-color: #666;">Logout</button>
  `;

  const charList = document.getElementById('character-list');
  if (state.characters.length === 0) {
    charList.innerHTML = '<p style="text-align: center; color: #999;">No characters yet. Create one to start playing!</p>';
  } else {
    state.characters.forEach(character => {
      const charEl = document.createElement('button');
      charEl.style.cssText = 'padding: 15px; text-align: left; cursor: pointer; border: 1px solid #ccc; background-color: #f5f5f5; border-radius: 4px;';
      charEl.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 5px;">${escapeHtml(character.name)}</div>
        <div style="font-size: 12px; color: #666;">Level ${character.level} | ${character.health} HP</div>
      `;
      charEl.addEventListener('click', async () => {
        const selectRes = await fetchJson(`/characters/${character.id}/select`, {
          method: 'POST'
        });
        if (selectRes.ok && selectRes.data.character) {
          if (selectRes.data.token) setAuthToken(selectRes.data.token);
          state.player = selectRes.data.character;
          navigateTo('/');
        }
      });
      charList.appendChild(charEl);
    });
  }

  const createCharNameInput = document.getElementById('create-char-name');

  document.getElementById('create-char-btn').addEventListener('click', async () => {
    const charName = createCharNameInput.value.trim() || 'Hero';
    const createRes = await fetchJson('/characters', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: charName })
    });
    if (createRes.ok && createRes.data) {
      state.characters = [...state.characters, createRes.data];
      await renderCharacterSelect();
    }
  });

  document.getElementById('logout-btn').addEventListener('click', async () => {
    await fetchJson('/login/signout', { method: 'POST' });
    clearAuthToken();
    state.currentUser = null;
    state.player = null;
    state.characters = [];
    navigateTo('/login');
  });
}

async function renderHome() {
  root.innerHTML = `<div class="game-container"><div id="main-content"></div></div>`;
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div class="home-layout">
      <div id="player-stats-container" class="home-panel home-stats-panel">
        <div id="player-stats"></div>
      </div>
      <div id="equip-panel" class="home-panel home-equip-panel"></div>
      <div class="inventory-panel-box home-panel home-inventory-panel">
        <div class="inventory-scroll-box">
          <div id="inventory-grid" class="inventory-grid"></div>
        </div>
      </div>
      <div class="clear-inventory-row" style="display:flex;justify-content:center;">
        <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:center;">
          <button class="dungeon-button clear-inventory-btn" id="clear-inventory-btn" style="background-color:#b23b3b;">Clear Inventory</button>
          <button type="button" class="dungeon-button trash-dropzone" id="inventory-trash-dropzone" aria-label="Trash inventory item" title="Drop inventory items here to delete" style="background-color:#5f6d7a;">🗑 Trash</button>
        </div>
      </div>
      <div class="home-actions-row" style="display:flex;justify-content:center;flex-wrap:wrap;gap:10px;margin-top:56px;">
        <button class="dungeon-button" id="enter-dungeon">Enter the Dungeon</button>
        <button class="dungeon-button" id="select-character-btn" style="background-color: #666;">Change Character</button>
        <button class="dungeon-button" id="logout-btn" style="background-color: #333;">Logout</button>
      </div>
    </div>
  `;

  document.getElementById('enter-dungeon').addEventListener('click', () => navigateTo('/dungeon'));
  document.getElementById('select-character-btn').addEventListener('click', () => navigateTo('/character-select'));

  document.getElementById('logout-btn').addEventListener('click', async () => {
    await fetchJson('/login/signout', { method: 'POST' });
    clearAuthToken();
    state.currentUser = null;
    state.player = null;
    state.characters = [];
    navigateTo('/login');
  });

  resetDungeonLoot();
  await loadStateAndRenderPartial();

  try {
    await syncPlayerHealthToFull();
    renderPlayerStatsInto(document.getElementById('player-stats'), state.player);
  } catch (error) {
    console.warn('Heal on home failed', error);
  }

  document.getElementById('clear-inventory-btn').addEventListener('click', async () => {
    const clearButton = document.getElementById('clear-inventory-btn');
    if (!clearButton) return;

    if (clearButton.dataset.confirmClear !== '1') {
      clearButton.dataset.confirmClear = '1';
      clearButton.textContent = 'Are you sure?';
      return;
    }

    try {
      clearButton.dataset.confirmClear = '0';
      clearButton.textContent = 'Clear Inventory';
      await clearUnequippedInventory();
    } catch (error) {
      console.error('Clear inventory failed', error);
    }
  });

  if (!document.documentElement.dataset.clearInventoryResetBound) {
    document.documentElement.dataset.clearInventoryResetBound = '1';
    document.addEventListener('click', event => {
      const clearButton = document.getElementById('clear-inventory-btn');
      if (!clearButton) return;
      if (clearButton.dataset.confirmClear !== '1') return;
      if (event.target.closest && event.target.closest('#clear-inventory-btn')) return;
      clearButton.dataset.confirmClear = '0';
      clearButton.textContent = 'Clear Inventory';
    });
  }

}

async function renderDungeon({ resetRunState = true } = {}) {
  if (resetRunState) resetDungeonLoot();
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
    syncPlayerSnapshot(playerResponse.data);
  }

  const encounterResponse = await fetchJson('/dungeon/enter', { method: 'POST' });
  const enemy = encounterResponse.ok ? encounterResponse.data : { name: '', health: 0, max_health: 0, damage: 0, description: '' };

  const preface = `A wild ${enemy.name || 'creature'} appears! ${enemy.description || ''}`;
  const messageToShow = state.lastDungeonMessage || preface;
  content.innerHTML = buildDungeonMarkup(enemy, messageToShow);

  renderPlayerStatsInto(document.getElementById('player-stats-container'), state.player);
  state.lastDungeonMessage = null;

  document.getElementById('attack').addEventListener('click', event => { event.preventDefault(); handleDungeonAttack(); });
  document.getElementById('run').addEventListener('click', event => { event.preventDefault(); handleDungeonRun(); });
  document.getElementById('back').addEventListener('click', event => {
    event.preventDefault();
    fetchJson('/dungeon/leave', { method: 'POST' }).finally(() => {
      resetDungeonLoot();
      navigateTo('/');
    });
  });
}

function navigateTo(path) {
  if (path === '/') location.hash = '#/'; else location.hash = `#${path}`;
}

async function route() {
  const hash = location.hash.replace('#', '') || '/';

  if (!state.currentUser && hash !== '/login') {
    const res = await fetchJson('/login/me');
    if (res.ok && res.data && res.data.user) {
      state.currentUser = res.data.user;
      if (res.data.character) syncPlayerSnapshot(res.data.character);
    } else {
      if (res.status === 401) clearAuthToken();
      location.hash = '#/login';
      return;
    }
  }

  if (hash === '/login') return renderLogin();
  if (hash === '/character-select') return renderCharacterSelect();
  if (hash === '/' || hash === '') return (state.player ? renderHome() : renderCharacterSelect());
  if (hash === '/dungeon') return renderDungeon();
  return renderHome();
}

export {
  navigateTo,
  route,
  renderLogin,
  renderCharacterSelect,
  renderHome,
  renderDungeon,
  loadStateAndRenderPartial,
};