/**
 * State management and synchronization utilities.
 * Centralizes app state mutations from multiple scattered functions in app-core.js.
 * All mutations happen through this module for better testability and maintainability.
 */

import { clearAuthToken } from '../api.js';

/**
 * Store the latest player data snapshot in app state.
 * Called after fetching character data from API.
 *
 * @param {Object} state - App state object (modified in place).
 * @param {Object} playerData - Character data from /characters/{id} endpoint.
 * @returns {void}
 */
export function syncPlayerSnapshot(state, playerData) {
  if (!state || !playerData) return;
  state.player = playerData;
}

/**
 * Clear the in-memory record of loot collected during current dungeon run.
 * Called when entering or exiting the dungeon to reset per-session loot tracking.
 *
 * @param {Object} state - App state object (modified in place).
 * @returns {void}
 */
export function resetDungeonLoot(state) {
  if (!state) return;
  state.lootCounts = {};
  state.activeCombat = null;
}

/**
 * Keep the in-memory player health synced to max health while on home views.
 * Called after major state changes that should reflect a fully-rested home state.
 *
 * @param {Object} state - App state object (modified in place).
 * @returns {Promise<Object>} Result object with updated player snapshot.
 */
export async function syncPlayerHealthToFull(state) {
  const player = state?.player;
  if (!player) return { ok: false };

  const maxHealth = Number(player.max_health);
  if (!Number.isFinite(maxHealth) || maxHealth < 0) return { ok: false };

  const nextPlayer = {
    ...player,
    health: maxHealth,
  };
  syncPlayerSnapshot(state, nextPlayer);
  return { ok: true, data: nextPlayer };
}

/**
 * Delete all unequipped inventory items and refresh the player view.
 * Called by the "Sell All" button on home screen.
 *
 * @param {Object} state - App state object (modified in place).
 * @param {number} userId - Current user ID.
 * @returns {Promise<Object>} Response from /users/{id}/inventory DELETE endpoint.
 */
export async function clearUnequippedInventory(fetchJson, state, userId) {
  if (!userId) return { ok: false };
  if (typeof fetchJson !== 'function') return { ok: false };

  const response = await fetchJson(`/users/${userId}/inventory`, {
    method: 'DELETE'
  });

  // After clearing, state will be refreshed by the caller via loadStateAndRenderPartial()
  return response;
}

/**
 * Clear the auth token and reset user/player state.
 * Called on logout or when auth fails.
 *
 * @param {Object} state - App state object (modified in place).
 * @returns {void}
 */
export function clearAuthState(state) {
  if (!state) return;
  state.currentUser = null;
  state.player = null;
  state.characters = [];
  state.inventory = [];
  state.equipped = [];
  state.activeCombat = null;
}

/**
 * Clear both cached auth and in-memory session state.
 * Shared by logout handlers across screens.
 */
export function clearSessionState(state) {
  clearAuthToken();
  clearAuthState(state);
}

/**
 * Sign out through the API and then clear the cached session state.
 * Shared by logout buttons on the auth and home screens.
 */
export async function signOutAndClearSession(fetchClient, state) {
  if (typeof fetchClient === 'function') {
    await fetchClient('/login/signout', { method: 'POST' });
  }
  clearSessionState(state);
}
