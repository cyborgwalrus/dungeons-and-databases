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

  /** Refresh the active character and re-render the shared HUD sections. */
  async function loadStateAndRenderPartial() {
    const characterId = state.player?.id;
    if (!characterId) return;

    // Refresh the cached player snapshot before repainting the HUD panels.
    const playerResponse = await fetchJson(`/characters/${characterId}`);
    if (playerResponse.ok && playerResponse.data) {
      syncPlayerSnapshot(state, playerResponse.data);
    }

    syncPlayerStatsInDom(state.player);
    renderEquipPanel();
    renderInventoryGrid();
  }

  /** Render the equipment panel using the current inventory snapshot. */
  function renderEquipPanel() {
    const equipped = Array.isArray(state.player?.equipped) ? state.player.equipped : [];
    return renderEquipPanelImpl({
      equipped,
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
    const inventory = Array.isArray(state.player?.inventory) ? state.player.inventory : [];
    const equipped = Array.isArray(state.player?.equipped) ? state.player.equipped : [];
    return renderInventoryGridImpl({
      inventory,
      equipped,
      fetchJson,
      loadStateAndRenderPartial,
      syncPlayerHealthToFull: () => syncPlayerHealthToFull(state),
      makeIcon,
      formatStats,
      getItemDisplayName,
    });
  }

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
      <div class="clear-inventory-row">
        <div class="clear-inventory-actions">
          <button class="dungeon-button dungeon-button-clear" id="clear-inventory-btn">Clear Inventory</button>
          <button type="button" class="dungeon-button dungeon-button-trash trash-dropzone" id="inventory-trash-dropzone" aria-label="Trash inventory item" title="Drop inventory items here to delete">🗑 Trash</button>
        </div>
      </div>
      <div class="home-actions-container">
        <button class="dungeon-button dungeon-button-primary" id="enter-dungeon">Enter the Dungeon</button>
        <button class="dungeon-button dungeon-button-secondary" id="select-character-btn">Change Character</button>
        <button class="dungeon-button dungeon-button-danger" id="logout-btn">Logout</button>
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
      clearButton.textContent = 'Clear Inventory';
      await clearUnequippedInventory(state, userId);
      await loadStateAndRenderPartial();
      await syncPlayerHealthToFull(state);
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
