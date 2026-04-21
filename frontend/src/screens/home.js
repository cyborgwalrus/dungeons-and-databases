/**
 * Home screen module.
 * Renders the player stats, equipment, inventory, and main navigation.
 */

import { 
  resetDungeonLoot, 
  syncPlayerHealthToFull, 
  clearUnequippedInventory, 
  syncPlayerSnapshot,
  signOutAndClearSession 
} from '../utils/state-updater.js';
import { renderPlayerStatsInto, syncPlayerStatsInDom } from '../components/player.js';
import { renderEquipPanel as renderEquipPanelImpl } from '../components/equip.js';
import { renderInventoryGrid as renderInventoryGridImpl } from '../components/inventory.js';
import { makeIcon, getItemDisplayName, formatStats } from '../helpers.js';
import { buildScreenShell } from '../ui.js';

/**
 * Render the home screen with inventory, equipment, and navigation actions.
 * 
 * @param {HTMLElement} root - Root DOM element to render into
 * @param {Object} deps - Dependencies object
 * @param {Function} deps.fetchJson - HTTP client for API calls
 * @param {Function} deps.navigateTo - Client-side router function
 * @param {Object} deps.state - App state object
 */
export async function renderHome(root, deps) {
  const { fetchJson, navigateTo, state } = deps;

  /** Fetch the current character, shared inventory, and equipped items separately. */
  async function loadCharacterViewModel() {
    const characterId = state.player?.id;
    const userId = state.currentUser?.id || state.player?.user_id;
    if (!characterId) return;

    const [characterResponse, inventoryResponse, equipmentResponse] = await Promise.all([
      fetchJson(`/characters/${characterId}`),
      userId ? fetchJson(`/users/${userId}/inventory`) : Promise.resolve({ ok: false, data: [] }),
      fetchJson(`/characters/${characterId}/equipment`),
    ]);

    if (characterResponse.ok && characterResponse.data) {
      syncPlayerSnapshot(state, characterResponse.data);
    }

    state.inventory = inventoryResponse.ok && Array.isArray(inventoryResponse.data) ? inventoryResponse.data : [];
    state.equipped = equipmentResponse.ok && Array.isArray(equipmentResponse.data) ? equipmentResponse.data : [];
  }

  /** Refresh the active character and re-render the shared HUD sections. */
  async function loadStateAndRenderPartial() {
    await loadCharacterViewModel();

    syncPlayerStatsInDom(state.player);
    renderEquipPanel();
    renderInventoryGrid();
  }

  /** Render the equipment panel using the current inventory snapshot. */
  function renderEquipPanel() {
    return renderEquipPanelImpl({
      equipped: Array.isArray(state.equipped) ? state.equipped : [],
      fetchJson,
      loadStateAndRenderPartial,
      syncPlayerHealthToFull: () => syncPlayerHealthToFull(state),
      makeIcon,
      formatStats,
      getItemDisplayName,
    });
  }

  /** Render the inventory grid using the current player snapshot. */
  function renderInventoryGrid() {
    return renderInventoryGridImpl({
      inventory: Array.isArray(state.inventory) ? state.inventory : [],
      equipped: Array.isArray(state.equipped) ? state.equipped : [],
      fetchJson,
      loadStateAndRenderPartial,
      syncPlayerHealthToFull: () => syncPlayerHealthToFull(state),
      makeIcon,
      formatStats,
      getItemDisplayName,
    });
  }

  root.innerHTML = buildScreenShell({
    className: 'screen-shell--game',
    title: 'Dungeons & Databases',
    subtitle: state.player?.name ? `${state.player.name} is ready` : 'Manage your character and inventory',
    sections: [{ id: 'main-content', body: 'Loading...' }],
  });
  const main = document.getElementById('main-content');
  main.innerHTML = `
    <div class="screen-stack home-stack">
      <div id="player-stats-container" class="screen-panel screen-panel--dark home-panel home-stats-panel">
        <div id="player-stats"></div>
      </div>
      <div id="equip-panel" class="screen-panel screen-panel--nested home-panel home-equip-panel"></div>
      <div class="screen-panel screen-panel--nested home-panel home-inventory-panel">
        <div class="inventory-management-box">
          <div class="inventory-panel-box">
            <div id="inventory-grid" class="inventory-grid"></div>
          </div>
          <div class="inventory-panel-box inventory-panel-box--sell-area">
            <div class="sell-area-content">
              <div
                id="inventory-sell-area-dropzone"
                class="inventory-scroll-box inventory-empty sell-area-dropzone"
                aria-label="Sell area"
                title="Drop inventory items here to sell"
              >
                <div class="inventory-empty-container">
                  <p class="inventory-empty-message">💰 Drag items here to sell.</p>
                </div>
              </div>
              <button class="dungeon-button dungeon-button-clear sell-all-btn" id="clear-inventory-btn">SELL\nALL</button>
            </div>
          </div>
        </div>
      </div>
      <div class="screen-panel screen-panel--dark home-actions-row">
        <div class="home-actions-container screen-button-stack">
          <button class="dungeon-button dungeon-button-primary" id="enter-dungeon">Enter the Dungeon</button>
          <button class="dungeon-button dungeon-button-secondary" id="select-character-btn">Change Character</button>
          <button class="dungeon-button dungeon-button-danger" id="logout-btn">Logout</button>
        </div>
      </div>
    </div>
  `;

  document.getElementById('enter-dungeon').addEventListener('click', () => navigateTo('/dungeon'));
  document.getElementById('select-character-btn').addEventListener('click', () => navigateTo('/character-select'));

  document.getElementById('logout-btn').addEventListener('click', async () => {
    await signOutAndClearSession(fetchJson, state);
    navigateTo('/login');
  });

  resetDungeonLoot(state);
  await loadStateAndRenderPartial();

  try {
    await syncPlayerHealthToFull(state);
    renderPlayerStatsInto(document.getElementById('player-stats'), state.player);
  } catch (error) {
    console.warn('Heal on home failed', error);
  }

  document.getElementById('clear-inventory-btn').addEventListener('click', async () => {
    const userId = state.currentUser?.id || state.player?.user_id;
    const clearButton = document.getElementById('clear-inventory-btn');
    if (!clearButton) return;

    if (clearButton.dataset.confirmClear !== '1') {
      clearButton.dataset.confirmClear = '1';
      clearButton.textContent = 'Are you sure?';
      return;
    }

    try {
      clearButton.dataset.confirmClear = '0';
      clearButton.textContent = 'SELL\nALL';
      await clearUnequippedInventory(state, userId);
      await loadStateAndRenderPartial();
      await syncPlayerHealthToFull(state);
    } catch (error) {
      console.error('Sell all failed', error);
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
      clearButton.textContent = 'SELL\nALL';
    });
  }
}
