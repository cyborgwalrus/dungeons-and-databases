import { getCharacterId } from '../app-state.js';

export const ITEM_DRAG_MIME = 'application/x-dd-item';

async function refreshCharacterAfterInventoryChange(opts) {
  const { loadStateAndRenderPartial, syncPlayerHealthToFull } = opts;
  await loadStateAndRenderPartial();
  if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
}

export function setItemDragData(event, data) {
  if (!event?.dataTransfer) return;
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData(ITEM_DRAG_MIME, JSON.stringify(data));
}

export function getItemDragData(event) {
  const rawData = event?.dataTransfer?.getData(ITEM_DRAG_MIME);
  if (!rawData) return null;
  try {
    return JSON.parse(rawData);
  } catch {
    return null;
  }
}

export async function equipInventoryItem(opts, itemId) {
  const { fetchJson } = opts;
  if (!itemId) return;
  const characterId = getCharacterId();
  if (!characterId) return;

  await fetchJson(`/characters/${characterId}/equipment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_id: Number(itemId) })
  });

  await refreshCharacterAfterInventoryChange(opts);
}

export async function unequipInventoryItem(opts, itemId) {
  const { fetchJson } = opts;
  if (!itemId) return;
  const characterId = getCharacterId();
  if (!characterId) return;

  await fetchJson(`/characters/${characterId}/equipment/${Number(itemId)}`, {
    method: 'DELETE'
  });

  await refreshCharacterAfterInventoryChange(opts);
}

export async function discardInventoryItem(opts, itemId) {
  const { fetchJson } = opts;
  if (!itemId) return;

  await fetchJson(`/items/${Number(itemId)}`, {
    method: 'DELETE'
  });

  await refreshCharacterAfterInventoryChange(opts);
}
