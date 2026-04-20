import { equipInventoryItem } from './item-actions.js';

export function renderInventoryGrid(opts) {
  const { inventory, equipped, fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull, getItemType, makeIcon, formatStats, getItemDisplayName } = opts;
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

  const equippedBySlot = new Map(
    (Array.isArray(equipped) ? equipped : [])
      .filter(Boolean)
      .map(item => [String(item.slot || '').toLowerCase(), item])
  );

  function getItemScore(item) {
    return (Number(item?.health) || 0) + (Number(item?.damage) || 0);
  }

  // Keep the strongest upgraded items near the top so equip scans are easier to follow.
  const sortedInventory = [...inventory].filter(Boolean).sort((a, b) => {
    const la = a.level || 1;
    const lb = b.level || 1;
    if (la !== lb) return lb - la;
    return (getItemDisplayName(a) || '').localeCompare(getItemDisplayName(b) || '');
  });

  const bestBySlot = new Map();
  sortedInventory.forEach(item => {
    const slot = String(item?.slot || '').toLowerCase();
    if (!slot) return;

    const currentBest = bestBySlot.get(slot);
    if (!currentBest) {
      bestBySlot.set(slot, item);
      return;
    }

    const currentScore = getItemScore(currentBest);
    const nextScore = getItemScore(item);
    if (nextScore > currentScore) {
      bestBySlot.set(slot, item);
      return;
    }

    if (nextScore === currentScore) {
      const currentLevel = Number(currentBest.level) || 1;
      const nextLevel = Number(item.level) || 1;
      if (nextLevel > currentLevel) {
        bestBySlot.set(slot, item);
      }
    }
  });

  function isBetterThanEquipped(item) {
    const slot = String(item?.slot || '').toLowerCase();
    if (!slot) return false;
    const bestItem = bestBySlot.get(slot);
    if (!bestItem || bestItem.id !== item.id) return false;
    const equippedItem = equippedBySlot.get(slot);
    return getItemScore(item) > getItemScore(equippedItem || { health: 0, damage: 0 });
  }

  const cards = [];
  sortedInventory.forEach(invItem => {
    const i = invItem;
    const itype = getItemType(i);
    const isBetter = isBetterThanEquipped(i);
    cards.push(`
      <button type="button" class="inventory-card${isBetter ? ' inventory-card--better' : ''}" data-item-id="${i.id}" data-item-type="${itype}">
        <div class="item-icon">${makeIcon(i)}</div>
        <div class="card-details">
          <div class="item-name">${getItemDisplayName(i)}</div>
          <div class="item-type${isBetter ? ' item-type--better' : ''}">${formatStats(i)}</div>
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
        await equipInventoryItem({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, itemId);
      } catch (error) {
        console.error('Failed to equip item from double click', error);
      }
    });
  });
}
