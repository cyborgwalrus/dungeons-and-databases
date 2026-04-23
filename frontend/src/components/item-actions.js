import { getCharacterId } from '../app-state.js';

export const ITEM_DRAG_MIME = 'application/x-dd-item';
const pendingItemActions = new Set();

function getPendingActionKey(action, itemId) {
  return `${action}:${Number(itemId)}`;
}

async function runOncePerItem(action, itemId, handler) {
  const key = getPendingActionKey(action, itemId);
  if (pendingItemActions.has(key)) return;

  pendingItemActions.add(key);
  try {
    await handler();
  } finally {
    pendingItemActions.delete(key);
  }
}

/** Re-render inventory state after an inventory mutation completes. */
async function refreshCharacterAfterInventoryChange(opts) {
  const { loadStateAndRenderPartial, syncPlayerHealthToFull } = opts;
  if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
  await loadStateAndRenderPartial();
}

/** Store item metadata on the drag event for later drop handling. */
export function setItemDragData(event, data) {
  if (!event?.dataTransfer) return;
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData(ITEM_DRAG_MIME, JSON.stringify(data));
}

/** Read item metadata back from a drag event payload. */
export function getItemDragData(event) {
  const rawData = event?.dataTransfer?.getData(ITEM_DRAG_MIME);
  if (!rawData) return null;
  try {
    return JSON.parse(rawData);
  } catch {
    return null;
  }
}

/** Equip an inventory item through the API and refresh the UI. */
export async function equipInventoryItem(opts, itemId) {
  const { fetchJson } = opts;
  if (!itemId) return;
  const characterId = getCharacterId();
  if (!characterId) return;

  await runOncePerItem('equip', itemId, async () => {
    await fetchJson(`/characters/${characterId}/equipment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: Number(itemId) })
    });

    await refreshCharacterAfterInventoryChange(opts);
  });
}

/** Unequip an item through the API and refresh the UI. */
export async function unequipInventoryItem(opts, itemId) {
  const { fetchJson } = opts;
  if (!itemId) return;
  const characterId = getCharacterId();
  if (!characterId) return;

  await runOncePerItem('unequip', itemId, async () => {
    await fetchJson(`/characters/${characterId}/equipment/${Number(itemId)}`, {
      method: 'DELETE'
    });

    await refreshCharacterAfterInventoryChange(opts);
  });
}

/** Delete an inventory item through the API and refresh the UI. */
export async function discardInventoryItem(opts, itemId) {
  const { fetchJson } = opts;
  if (!itemId) return;

  await runOncePerItem('discard', itemId, async () => {
    await fetchJson(`/items/${Number(itemId)}`, {
      method: 'DELETE'
    });

    await refreshCharacterAfterInventoryChange(opts);
  });
}
