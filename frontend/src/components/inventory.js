import { discardInventoryItem, equipInventoryItem, getItemDragData, setItemDragData, unequipInventoryItem } from './item-actions.js';
import { setupDragDropZone } from '../utils/drag-drop.js';
import { scoreItem, buildEquippedSlotMap } from '../utils/inventory-utils.js';

/**
 * Render the inventory grid and wire up drag/drop interactions.
 * Uses standardized drag/drop utilities to reduce code duplication.
 */
export function renderInventoryGrid(opts) {
  const { inventory, equipped, fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull, getItemType, makeIcon, formatStats, getItemDisplayName } = opts;
  const invContainer = document.getElementById('inventory-grid');
  if (!invContainer) return;
  const scrollBox = invContainer.closest('.inventory-scroll-box');
  const dropZone = scrollBox || invContainer;
  const itemCount = Array.isArray(inventory) ? inventory.length : 0;
  if (scrollBox) {
    scrollBox.classList.toggle('inventory-empty', itemCount === 0);
    scrollBox.style.maxHeight = itemCount > 5 ? '390px' : 'none';
  }

  // Build efficient slot → item lookup for equipped items
  const equippedBySlot = buildEquippedSlotMap(equipped);

  // Sort inventory by level and name for consistent display
  const sortedInventory = [...(inventory || [])].filter(Boolean).sort((a, b) => {
    const la = a.level || 1;
    const lb = b.level || 1;
    if (la !== lb) return lb - la;
    return (getItemDisplayName(a) || '').localeCompare(getItemDisplayName(b) || '');
  });

  // Track best item per slot for upgrade highlighting
  const bestBySlot = new Map();
  sortedInventory.forEach(item => {
    const slot = String(item?.slot || '').toLowerCase();
    if (!slot) return;

    const currentBest = bestBySlot.get(slot);
    if (!currentBest) {
      bestBySlot.set(slot, item);
      return;
    }

    const currentScore = scoreItem(currentBest);
    const nextScore = scoreItem(item);
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

  /**
   * Determine if an item is better than what's currently equipped.
   * Used to highlight upgrades in the inventory grid.
   */
  function isBetterThanEquipped(item) {
    const slot = String(item?.slot || '').toLowerCase();
    if (!slot) return false;
    const bestItem = bestBySlot.get(slot);
    if (!bestItem || bestItem.id !== item.id) return false;
    const equippedItem = equippedBySlot[slot];
    return scoreItem(item) > scoreItem(equippedItem || { health: 0, damage: 0 });
  }

  if (!inventory || inventory.length === 0) {
    invContainer.innerHTML = '<div class="inventory-empty-container"><p class="inventory-empty-message">Your inventory is empty.</p><p class="inventory-empty-note">Note: the inventory is shared between characters.</p></div>';
  } else {
    const cards = [];
    sortedInventory.forEach(invItem => {
      const i = invItem;
      const itype = getItemType(i);
      const isBetter = isBetterThanEquipped(i);
      cards.push(`
        <button type="button" draggable="true" class="inventory-card${isBetter ? ' inventory-card--better' : ''}" data-item-id="${i.id}" data-item-type="${itype}" data-item-source="inventory">
          <div class="item-icon">${makeIcon(i)}</div>
          <div class="card-details">
            <div class="item-name">${getItemDisplayName(i)}</div>
            <div class="item-type${isBetter ? ' item-type--better' : ''}">${formatStats(i)}</div>
          </div>
        </button>`);
    });
    invContainer.innerHTML = cards.join('');
  }

  // Setup inventory area as drop zone for unequipping items
  setupDragDropZone(dropZone, {
    validatePayload: (event) => {
      const payload = getItemDragData(event);
      return payload && payload.source === 'equipped' ? payload : null;
    },
    onDrop: async (payload) => {
      try {
        await unequipInventoryItem({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, payload.itemId);
      } catch (error) {
        console.error('Failed to unequip item from drag and drop', error);
      }
    },
    activeClass: 'inventory-dropzone--active'
  });

  // Setup trash zone as drop zone for discarding items
  const trashDropzone = document.getElementById('inventory-trash-dropzone');
  if (trashDropzone) {
    setupDragDropZone(trashDropzone, {
      validatePayload: (event) => {
        const payload = getItemDragData(event);
        return payload && payload.source === 'inventory' ? payload : null;
      },
      onDrop: async (payload) => {
        try {
          await discardInventoryItem({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, payload.itemId);
        } catch (error) {
          console.error('Failed to discard item from drag and drop', error);
        }
      },
      activeClass: 'trash-dropzone--active'
    });
  }

  // Setup inventory cards as draggable items
  document.querySelectorAll('.inventory-card').forEach(card => {
    card.addEventListener('dragstart', event => {
      setItemDragData(event, {
        itemId: Number(card.getAttribute('data-item-id')),
        source: card.getAttribute('data-item-source') || 'inventory',
      });
      card.classList.add('dragging');
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
    });

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

