import { discardInventoryItem, equipInventoryItem, getItemDragData, unequipInventoryItem } from './item-actions.js';
import { setupDragDropZone, setupDraggableItem } from '../utils/drag-drop.js';
import { scoreItem, buildEquippedSlotMap } from '../utils/inventory-utils.js';
import { renderItemCardHtml } from './item-card.js';

/**
 * Render the inventory grid and wire up drag/drop interactions.
 * Uses standardized drag/drop utilities to reduce code duplication.
 */
export function renderInventoryGrid(opts) {
  const { inventory, equipped, fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull, makeIcon, formatStats, getItemDisplayName } = opts;
  const invContainer = document.getElementById('inventory-grid');
  if (!invContainer) return;
  const dropZone = invContainer;

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
    const slot = String(item?.slot_type || '').toLowerCase();
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
    const slot = String(item?.slot_type || '').toLowerCase();
    if (!slot) return false;
    const bestItem = bestBySlot.get(slot);
    if (!bestItem || bestItem.id !== item.id) return false;
    const equippedItem = equippedBySlot[slot];
    return scoreItem(item) > scoreItem(equippedItem || { health: 0, damage: 0 });
  }

  if (!inventory || inventory.length === 0) {
    invContainer.innerHTML = '<div class="inventory-empty-container"><p class="inventory-empty-message">Your inventory is empty.</p><p class="inventory-empty-note">Note: the inventory is shared between characters.</p></div>';
  } else {
    invContainer.innerHTML = sortedInventory.map(invItem => {
      const isBetter = isBetterThanEquipped(invItem);
      return renderItemCardHtml(invItem, {
        source: 'inventory',
        icon: makeIcon(invItem),
        name: getItemDisplayName(invItem),
        stats: formatStats(invItem),
        better: isBetter,
      });
    }).join('');
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
  const sellAreaDropzone = document.getElementById('inventory-sell-area-dropzone');
  if (sellAreaDropzone) {
    setupDragDropZone(sellAreaDropzone, {
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
      activeClass: 'sell-area-dropzone--active'
    });
  }

  // Setup inventory cards as draggable items
  document.querySelectorAll('.inventory-card').forEach(card => {
    setupDraggableItem(card, {
      dragData: {
        itemId: Number(card.getAttribute('data-item-id')),
        source: card.getAttribute('data-item-source') || 'inventory',
        slot_type: card.getAttribute('data-item-slot-type') || '',
          actionHref: card.getAttribute('data-item-equip-href') || '',
      }
    });

    card.addEventListener('dblclick', async event => {
      event.preventDefault();
      event.stopPropagation();
        const itemRef = {
          itemId: Number(card.getAttribute('data-item-id')),
          actionHref: card.getAttribute('data-item-equip-href') || '',
        };
      try {
          await equipInventoryItem({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, itemRef);
      } catch (error) {
        console.error('Failed to equip item from double click', error);
      }
    });
  });
}

