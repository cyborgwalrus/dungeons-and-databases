import { getCharacterId } from '../app-state.js';

export const ITEM_DRAG_MIME = 'application/x-dd-item';

function resolveItemActionPath(itemRef, action, characterId) {
  const itemId = typeof itemRef === 'object' ? itemRef?.itemId ?? itemRef?.id : itemRef;
  const href = typeof itemRef === 'object'
    ? (action === 'equip' ? itemRef.equipHref : itemRef.unequipHref)
    : null;

  if (href) return href;
  if (!characterId || !itemId) return null;
  return `/characters/${characterId}/equipment/${Number(itemId)}`;
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

  const requestPath = resolveItemActionPath(itemId, 'equip', characterId);
  if (!requestPath) return;

  await fetchJson(requestPath, {
    method: 'POST',
  });

  await refreshCharacterAfterInventoryChange(opts);
}

/** Unequip an item through the API and refresh the UI. */
export async function unequipInventoryItem(opts, itemId) {
  const { fetchJson } = opts;
  if (!itemId) return;
  const characterId = getCharacterId();
  if (!characterId) return;

  const requestPath = resolveItemActionPath(itemId, 'unequip', characterId);
  if (!requestPath) return;

  await fetchJson(requestPath, {
    method: 'DELETE'
  });

  await refreshCharacterAfterInventoryChange(opts);
}

/** Delete an inventory item through the API and refresh the UI. */
export async function discardInventoryItem(opts, itemId) {
  const { fetchJson } = opts;
  if (!itemId) return;

  await fetchJson(`/items/${Number(itemId)}`, {
    method: 'DELETE'
  });

  await refreshCharacterAfterInventoryChange(opts);
}
