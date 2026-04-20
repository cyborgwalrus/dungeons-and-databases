import { getCharacterId } from '../app-state.js';

async function toggleInventoryItemFromDoubleClick(opts, itemId) {
  const { fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull } = opts;
  if (!itemId) return;
  const characterId = getCharacterId();
  if (!characterId) return;

  await fetchJson(`/characters/${characterId}/equipment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_id: Number(itemId) })
  });

  await loadStateAndRenderPartial();
  if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
}

export function renderInventoryGrid(opts) {
  const { inventory, fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull, getItemType, makeIcon, formatStats, getItemDisplayName } = opts;
  const invContainer = document.getElementById('inventory-grid');
  if (!invContainer) return;
  const scrollBox = invContainer.closest('.inventory-scroll-box');
  const itemCount = Array.isArray(inventory) ? inventory.length : 0;
  if (scrollBox) {
    scrollBox.classList.toggle('inventory-empty', itemCount === 0);
    scrollBox.style.maxHeight = itemCount > 5 ? '390px' : 'none';
  }
  if (!inventory || inventory.length === 0) {
    invContainer.innerHTML = '<p style="color:#999;font-style:italic">Your inventory is empty</p>';
    return;
  }

  // Keep the strongest upgraded items near the top so equip scans are easier to follow.
  const sortedInventory = [...inventory].filter(Boolean).sort((a, b) => {
    const la = a.level || 1;
    const lb = b.level || 1;
    if (la !== lb) return lb - la;
    return (getItemDisplayName(a) || '').localeCompare(getItemDisplayName(b) || '');
  });

  const cards = [];
  sortedInventory.forEach(invItem => {
    const i = invItem;
    const itype = getItemType(i);
    cards.push(`
      <button type="button" class="inventory-card" data-item-id="${i.id}" data-item-type="${itype}">
        <div class="item-icon">${makeIcon(i)}</div>
        <div class="card-details">
          <div class="item-name">${getItemDisplayName(i)}</div>
          <div class="item-type">${formatStats(i)}</div>
        </div>
      </button>`);
  });
  invContainer.innerHTML = cards.join('');

  document.querySelectorAll('.inventory-card').forEach(card => {
    card.addEventListener('dblclick', async event => {
      event.preventDefault();
      event.stopPropagation();
      const itemId = card.getAttribute('data-item-id');
      try {
        await toggleInventoryItemFromDoubleClick({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, itemId);
      } catch (error) {
        console.error('Failed to equip item from double click', error);
      }
    });
  });
}
