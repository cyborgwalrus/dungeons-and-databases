/**
 * State management and synchronization utilities.
 * Centralizes app state mutations from multiple scattered functions in app-core.js.
 * All mutations happen through this module for better testability and maintainability.
 */

import { fetchJson, clearAuthToken } from '../api.js';
import { getCharacterId } from '../app-state.js';

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
}

/**
 * Refresh active character and request full heal from API.
 * Called after major state changes (e.g., equipping items) to get current health.
 *
 * @param {Object} state - App state object (modified in place).
 * @returns {Promise<Object>} Response from /characters/{id}/full_heal endpoint.
 */
export async function syncPlayerHealthToFull(state) {
  const characterId = getCharacterId();
  if (!characterId) return { ok: false };

  const response = await fetchJson(`/characters/${characterId}/full_heal`, {
    method: 'POST'
  });

  if (response.ok && response.data) {
    syncPlayerSnapshot(state, response.data);
  }

  return response;
}

/**
 * Delete all unequipped inventory items and refresh the player view.
 * Called by the "Sell All" button on home screen.
 *
 * @param {Object} state - App state object (modified in place).
 * @param {number} userId - Current user ID.
 * @returns {Promise<Object>} Response from /users/{id}/inventory DELETE endpoint.
 */
export async function clearUnequippedInventory(state, userId) {
  if (!userId) return { ok: false };

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
