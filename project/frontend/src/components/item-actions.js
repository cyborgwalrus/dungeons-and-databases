import { getCharacterId } from '../app-state.js';

async function refreshCharacterAfterInventoryChange(opts) {
  const { loadStateAndRenderPartial, syncPlayerHealthToFull } = opts;
  await loadStateAndRenderPartial();
  if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
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
